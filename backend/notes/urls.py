from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import NoteViewSet, PublicNoteView, TagListView

router = SimpleRouter(trailing_slash=False)
router.register(r"notes", NoteViewSet, basename="notes")

urlpatterns = router.urls + [
    path("tags", TagListView.as_view(), name="tags"),
    path("tags/", TagListView.as_view()),
    path("public/notes/<str:token>", PublicNoteView.as_view(), name="public-note"),
    path("public/notes/<str:token>/", PublicNoteView.as_view()),
]
