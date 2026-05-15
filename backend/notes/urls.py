from django.urls import re_path
from rest_framework.routers import SimpleRouter

from .views import NoteViewSet, PublicNoteView, TagListView

router = SimpleRouter(trailing_slash=False)
router.register(r"notes", NoteViewSet, basename="notes")

urlpatterns = router.urls + [
    re_path(r"^tags/?$", TagListView.as_view(), name="tags"),
    re_path(r"^public/notes/(?P<token>[^/]+)/?$", PublicNoteView.as_view(), name="public-note"),
]
