import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


COLOR_CHOICES = [
    ("default", "Default"),
    ("yellow", "Yellow"),
    ("green", "Green"),
    ("blue", "Blue"),
    ("pink", "Pink"),
    ("purple", "Purple"),
    ("orange", "Orange"),
    ("gray", "Gray"),
]


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=40)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tags"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("owner", "name")]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes"
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, default="")
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="default")
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True, related_name="notes")
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="NoteShare",
        through_fields=("note", "user"),
        related_name="shared_notes",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]
        indexes = [
            models.Index(fields=["owner", "-updated_at"]),
            models.Index(fields=["owner", "is_pinned", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Note {self.id}"


class NoteShare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="shares")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="note_shares"
    )
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shares_given",
    )
    can_edit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("note", "user")]
        ordering = ["-created_at"]


def _generate_token() -> str:
    return secrets.token_urlsafe(24)


class PublicShareLink(models.Model):
    """Custom feature: anyone with the token can read the note (no auth)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.OneToOneField(Note, on_delete=models.CASCADE, related_name="public_link")
    token = models.CharField(max_length=64, unique=True, default=_generate_token, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= timezone.now()
