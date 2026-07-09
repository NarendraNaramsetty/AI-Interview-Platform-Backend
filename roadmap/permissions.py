from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Access controls:
    - Users can view and CRUD only their own reminders and roadmaps progress.
    - Admins can manage all roadmap resources.
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
        if hasattr(obj, 'user_roadmap'):
            return obj.user_roadmap.user == request.user

        return False
