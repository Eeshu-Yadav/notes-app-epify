from rest_framework import permissions

from .models import Note


class IsOwnerOrSharedReadOnly(permissions.BasePermission):
    """Owner has full access; users in shared_with can read; others denied."""

    def has_object_permission(self, request, view, obj: Note) -> bool:
        if obj.owner_id == request.user.id:
            return True
        if request.method in permissions.SAFE_METHODS:
            return obj.shares.filter(user=request.user).exists()
        share = obj.shares.filter(user=request.user).first()
        return bool(share and share.can_edit)


class IsOwner(permissions.BasePermission):
    """Strict: only owner can perform the action (used for share/delete/public-link)."""

    def has_object_permission(self, request, view, obj) -> bool:
        owner_id = getattr(obj, "owner_id", None) or getattr(getattr(obj, "note", None), "owner_id", None)
        return owner_id == request.user.id
