from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Note, NoteShare, PublicShareLink, Tag, _generate_token
from .permissions import IsOwnerOrSharedReadOnly
from .serializers import (
    NoteShareInputSerializer,
    NoteSerializer,
    PublicNoteSerializer,
    PublicShareLinkSerializer,
    TagSerializer,
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="List notes (owned + shared) with filters & pagination",
        tags=["notes"],
        parameters=[
            OpenApiParameter("page", int, description="Page number"),
            OpenApiParameter("page_size", int, description="Items per page (max 100)"),
            OpenApiParameter("pinned", str, description="true / false"),
            OpenApiParameter("archived", str, description="true / false (default false)"),
            OpenApiParameter("color", str, description="Filter by color label"),
            OpenApiParameter("tag", str, description="Filter by tag name"),
        ],
    ),
    retrieve=extend_schema(summary="Get a note by id (owner or shared user)", tags=["notes"]),
    create=extend_schema(summary="Create a new note", tags=["notes"]),
    update=extend_schema(summary="Update a note (full)", tags=["notes"]),
    partial_update=extend_schema(summary="Update a note (partial)", tags=["notes"]),
    destroy=extend_schema(summary="Delete a note (owner only)", tags=["notes"]),
)
class NoteViewSet(viewsets.ModelViewSet):
    """CRUD for notes. Owner has full access; shared users can read (or edit if granted)."""

    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSharedReadOnly]
    queryset = Note.objects.none()
    lookup_value_regex = r"[0-9a-f-]{36}"

    def get_queryset(self):
        user = self.request.user
        qs = Note.objects.filter(
            Q(owner=user) | Q(shares__user=user)
        ).distinct().prefetch_related("tags", "shares__user").select_related("owner")

        params = self.request.query_params
        if params.get("pinned") in ("true", "1"):
            qs = qs.filter(is_pinned=True)
        elif params.get("pinned") in ("false", "0"):
            qs = qs.filter(is_pinned=False)

        archived = params.get("archived")
        if archived in ("true", "1"):
            qs = qs.filter(is_archived=True)
        else:
            qs = qs.filter(is_archived=False)

        if color := params.get("color"):
            qs = qs.filter(color=color)
        if tag := params.get("tag"):
            qs = qs.filter(tags__name__iexact=tag.strip().lower())
        return qs

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
        can_edit = serializer.validated_data.get("can_edit", False)
        share, created = NoteShare.objects.get_or_create(
            note=note, user=target,
            defaults={"shared_by": request.user, "can_edit": can_edit},
        )
        if not created:
            share.can_edit = can_edit
            share.save(update_fields=["can_edit"])
        return Response({
            "message": f"Note shared with {target.email}",
            "share_with_email": target.email,
            "can_edit": share.can_edit,
            "already_shared": not created,
        })

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
        summary="Create/rotate (POST) or revoke (DELETE) a public share link",
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
        link, created = PublicShareLink.objects.get_or_create(note=note)
        if not created:
            link.token = _generate_token()
        link.expires_at = request.data.get("expires_at") or None
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
    queryset = Tag.objects.none()

    def get_queryset(self):
        return Tag.objects.filter(owner=self.request.user)


class PublicNoteView(generics.RetrieveAPIView):
    """Anyone with the token can read; increments view_count."""

    permission_classes = [AllowAny]
    serializer_class = PublicNoteSerializer
    authentication_classes = []

    def get_object(self):
        token = self.kwargs.get("token", "")
        try:
            link = PublicShareLink.objects.select_related("note__owner").get(token=token)
        except PublicShareLink.DoesNotExist:
            raise NotFound("Public link not found or revoked.")
        if link.is_expired():
            raise NotFound("This public link has expired.")
        PublicShareLink.objects.filter(pk=link.pk).update(view_count=link.view_count + 1)
        return link.note

    @extend_schema(summary="Public read access to a note via token (no auth)", tags=["public-share"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
