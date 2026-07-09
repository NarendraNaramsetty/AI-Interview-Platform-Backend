from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Access controls:
    - Standard candidates can CRUD only their own chat sessions, messages, feedback, and bookmarks.
    - Admins can manage prompt templates and search all sessions.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin override
        if request.user.is_staff:
            return True

        # Check model ownership fields
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'session'):
            return obj.session.user == request.user
        if hasattr(obj, 'chat_message'):
            return obj.chat_message.session.user == request.user

        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permissions check allowing anyone to read prompts, but restricting creation/edits to Admins.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_staff
