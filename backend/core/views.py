from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notes.models import Note
from notes.serializers import NoteSerializer


class AboutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(summary="About this service", tags=["meta"])
    def get(self, request):
        return Response({
            "name": "Eeshu Yadav",
            "email": "eeshu.yadav@primathon.in",
            "my features": {
                "Public Share Links": "Owners can generate a tokenized public read-only URL for any note (with optional expiry) that anyone can open without an account — like Google Docs share-by-link. I picked this because real notes apps need a frictionless way to share with non-users; building it forced me to design a no-auth read path, model token rotation/revocation, and protect the rest of the API behind JWT.",
                "Pinning, Color Labels & Tags": "Google-Keep-style organization: pin notes to the top, assign one of eight color labels, and add free-form tags. Demonstrates many-to-many modeling (tags), per-user uniqueness, and shows product sense for how users actually browse a multi-note workspace.",
                "Sharing with Edit Permissions": "Beyond the spec's read-only share, sharing also accepts `can_edit` so collaborators can update content — useful for couples/teams sharing a single shopping list or doc.",
                "Full-text Search & Pagination": "Stretch goals — `GET /search?q=` covers title+content+tag matches across notes the user can access, and `GET /notes` is paginated with `page` / `page_size`."
            }
        })


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        return Response({"status": "ok"})


class SearchView(APIView):
    """Full-text search across title, content, and tag names for notes the user can access."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter("q", str, required=True, description="Search keyword")],
        summary="Full-text search across user's notes",
        tags=["notes"],
    )
    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        if not q:
            return Response({"detail": "Query parameter 'q' is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        qs = (
            Note.objects
            .filter(Q(owner=user) | Q(shares__user=user))
            .filter(
                Q(title__icontains=q)
                | Q(content__icontains=q)
                | Q(tags__name__icontains=q.lower())
            )
            .distinct()
            .prefetch_related("tags", "shares__user")
            .select_related("owner")
        )
        page_size = min(int(request.query_params.get("page_size", 20) or 20), 100)
        results = list(qs[:page_size])
        return Response({
            "query": q,
            "count": len(results),
            "results": NoteSerializer(results, many=True, context={"request": request}).data,
        })
