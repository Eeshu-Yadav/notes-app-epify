from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import COLOR_CHOICES, Note, NoteShare, PublicShareLink, Tag

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "created_at")
        read_only_fields = ("id", "created_at")


class NoteSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=40, allow_blank=False),
        required=False,
        write_only=True,
        help_text="Tag names. New ones are created on the fly.",
    )
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    shared_with = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    public_link = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = (
            "id", "title", "content", "color", "is_pinned", "is_archived",
            "tags", "tags_detail", "owner_email", "shared_with", "is_owner",
            "public_link", "created_at", "updated_at",
        )
        read_only_fields = ("id", "owner_email", "shared_with", "is_owner",
                            "public_link", "tags_detail", "created_at", "updated_at")

    def get_shared_with(self, obj):
        return [s.user.email for s in obj.shares.all().select_related("user")]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.owner_id == request.user.id)

    def get_public_link(self, obj):
        link = getattr(obj, "public_link", None)
        if link is None:
            return None
        return {
            "token": link.token,
            "expires_at": link.expires_at,
            "view_count": link.view_count,
        }

    def validate_title(self, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_color(self, value: str) -> str:
        valid = {c[0] for c in COLOR_CHOICES}
        if value not in valid:
            raise serializers.ValidationError(f"Invalid color. Must be one of {sorted(valid)}.")
        return value

    def _set_tags(self, note: Note, tag_names: list[str]) -> None:
        cleaned = []
        seen = set()
        for raw in tag_names:
            name = (raw or "").strip().lower()
            if not name or name in seen:
                continue
            seen.add(name)
            cleaned.append(name[:40])
        tags = []
        for name in cleaned:
            tag, _ = Tag.objects.get_or_create(owner=note.owner, name=name)
            tags.append(tag)
        note.tags.set(tags)

    def create(self, validated_data):
        tag_names = validated_data.pop("tags", None)
        note = Note.objects.create(owner=self.context["request"].user, **validated_data)
        if tag_names is not None:
            self._set_tags(note, tag_names)
        return note

    def update(self, instance, validated_data):
        tag_names = validated_data.pop("tags", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if tag_names is not None:
            self._set_tags(instance, tag_names)
        return instance


class NoteShareInputSerializer(serializers.Serializer):
    share_with_email = serializers.EmailField()
    can_edit = serializers.BooleanField(required=False, default=False)


class PublicShareLinkSerializer(serializers.ModelSerializer):
    public_url_path = serializers.SerializerMethodField()

    class Meta:
        model = PublicShareLink
        fields = ("token", "expires_at", "view_count", "public_url_path", "created_at")
        read_only_fields = ("token", "view_count", "public_url_path", "created_at")

    def get_public_url_path(self, obj):
        return f"/public/notes/{obj.token}"


class PublicNoteSerializer(serializers.ModelSerializer):
    owner_email = serializers.CharField(source="owner.email", read_only=True)

    class Meta:
        model = Note
        fields = ("id", "title", "content", "color", "owner_email", "created_at", "updated_at")
        read_only_fields = fields
