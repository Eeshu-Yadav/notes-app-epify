from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Note, NoteShare, PublicShareLink, Tag
from .permissions import IsOwnerOrSharedReadOnly
from .serializers import (
    NoteShareInputSerializer,
    NoteSerializer,
    PublicNoteSerializer,
    PublicShareLinkSerializer,
    TagSerializer,
)

User = get_user_model()


class NoteViewSet(viewsets.ModelViewSet):
    """CRUD for notes. Owner has full access; shared users can read (or edit if granted)."""

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSharedReadOnly]
    lookup_value_regex = r"[0-9a-f-]{36}"

    def get_queryset(self):
        user = self.request.user
        qs = Note.objects.filter(
            Q(owner=user) | Q(shares__user=user)
        ).distinct().prefetch_related("tags", "shares__user").select_related("owner")

        pinned = self.request.query_params.get("pinned")
        if pinned in ("true", "1"):
            qs = qs.filter(is_pinned=True)
        elif pinned in ("false", "0"):
            qs = qs.filter(is_pinned=False)

        archived = self.request.query_params.get("archived")
        if archived in ("true", "1"):
            qs = qs.filter(is_archived=True)
        elif archived in ("false", "0", None, ""):
            qs = qs.filter(is_archived=False)

        color = self.request.query_params.get("color")
        if color:
            qs = qs.filter(color=color)

        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__name__iexact=tag.strip().lower())

        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter("page", int, description="Page number for pagination"),
            OpenApiParameter("page_size", int, description="Items per page (max 100)"),
            OpenApiParameter("pinned", str, description="Filter: true/false"),
            OpenApiParameter("archived", str, description="Filter: true/false (default false)"),
            OpenApiParameter("color", str, description="Filter by color label"),
            OpenApiParameter("tag", str, description="Filter by tag name"),
        ],
        summary="List notes (owned + shared) with filters & pagination",
        tags=["notes"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Get a note by id (owner or shared user)", tags=["notes"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Create a new note", tags=["notes"])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update a note (full)", tags=["notes"])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Update a note (partial)", tags=["notes"])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a note (owner only)", tags=["notes"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner_id != request.user.id:
            return Response({"detail": "Only the owner can delete this note."},
                            status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=NoteShareInputSerializer,
        responses={200: OpenApiResponse(description="Note shared")},
        summary="Share a note with another user by email",
        tags=["notes"],
    )
    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        note = self.get_object()
        if note.owner_id != request.user.id:
            return Response({"detail": "Only the owner can share this note."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = NoteShareInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_email = serializer.validated_data["share_with_email"].strip().lower()
        if target_email == request.user.email.lower():
            return Response({"detail": "You cannot share a note with yourself."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            target = User.objects.get(email__iexact=target_email)
        except User.DoesNotExist:
            return Response({"detail": "User with that email does not exist."},
                            status=status.HTTP_404_NOT_FOUND)
        share, created = NoteShare.objects.get_or_create(
            note=note,
            user=target,
            defaults={
                "shared_by": request.user,
                "can_edit": serializer.validated_data.get("can_edit", False),
            },
        )
        if not created:
            share.can_edit = serializer.validated_data.get("can_edit", share.can_edit)
            share.save()
        return Response(
            {
                "message": f"Note shared with {target.email}",
                "share_with_email": target.email,
                "can_edit": share.can_edit,
                "already_shared": not created,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        responses={200: OpenApiResponse(description="Sharing revoked")},
        summary="Revoke sharing for a specific user",
        tags=["notes"],
    )
    @action(detail=True, methods=["post"], url_path="unshare")
    def unshare(self, request, pk=None):
        note = self.get_object()
        if note.owner_id != request.user.id:
            return Response({"detail": "Only the owner can revoke sharing."},
                            status=status.HTTP_403_FORBIDDEN)
        email = (request.data.get("share_with_email") or "").strip().lower()
        if not email:
            return Response({"detail": "share_with_email is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = NoteShare.objects.filter(note=note, user__email__iexact=email).delete()
        if not deleted:
            return Response({"detail": "No active share for that email."},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"Sharing revoked for {email}"})

    @extend_schema(
        responses={201: PublicShareLinkSerializer, 200: PublicShareLinkSerializer,
                   204: OpenApiResponse(description="Public link revoked")},
        summary="Create/rotate (POST) or revoke (DELETE) a public share link for a note",
        tags=["public-share"],
    )
    @action(detail=True, methods=["post", "delete"], url_path="public-link")
    def public_link(self, request, pk=None):
        note = self.get_object()
        if note.owner_id != request.user.id:
            return Response({"detail": "Only the owner can manage the public link."},
                            status=status.HTTP_403_FORBIDDEN)
        if request.method == "DELETE":
            PublicShareLink.objects.filter(note=note).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        expires_at = request.data.get("expires_at") or None
        link, created = PublicShareLink.objects.get_or_create(note=note)
        if not created:
            from .models import _generate_token
            link.token = _generate_token()
        link.expires_at = expires_at or None
        link.save()
        return Response(
            PublicShareLinkSerializer(link).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(summary="Toggle pin on a note", tags=["notes"])
    @action(detail=True, methods=["post"], url_path="toggle-pin")
    def toggle_pin(self, request, pk=None):
        note = self.get_object()
        if note.owner_id != request.user.id:
            return Response({"detail": "Only the owner can pin/unpin."},
                            status=status.HTTP_403_FORBIDDEN)
        note.is_pinned = not note.is_pinned
        note.save(update_fields=["is_pinned", "updated_at"])
        return Response(NoteSerializer(note, context={"request": request}).data)


class TagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tag.objects.filter(owner=self.request.user)


class PublicNoteView(generics.RetrieveAPIView):
    """Anyone with the token can read; increments view_count."""

    permission_classes = [AllowAny]
    serializer_class = PublicNoteSerializer
    authentication_classes: list = []

    def get_object(self):
        token = self.kwargs.get("token", "")
        try:
            link = PublicShareLink.objects.select_related("note__owner").get(token=token)
        except PublicShareLink.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Public link not found or revoked.")
        if link.is_expired():
            from rest_framework.exceptions import NotFound
            raise NotFound("This public link has expired.")
        PublicShareLink.objects.filter(pk=link.pk).update(view_count=link.view_count + 1)
        return link.note

    @extend_schema(summary="Public read access to a note via token (no auth)", tags=["public-share"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
