from django.contrib import admin

from .models import Note, NoteShare, PublicShareLink, Tag


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "color", "is_pinned", "updated_at")
    list_filter = ("color", "is_pinned", "is_archived")
    search_fields = ("title", "content", "owner__email")


@admin.register(NoteShare)
class NoteShareAdmin(admin.ModelAdmin):
    list_display = ("note", "user", "shared_by", "created_at")
    search_fields = ("note__title", "user__email")


@admin.register(PublicShareLink)
class PublicShareLinkAdmin(admin.ModelAdmin):
    list_display = ("note", "token", "view_count", "expires_at", "created_at")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__email")
