from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Access policy:
    - Candidates can view/modify only their own drafts and submissions.
    - Admin staff users can manage all objects globally.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin bypass
        if request.user.is_staff:
            return True

        # Check user fields on standard models
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'submission'):
            return obj.submission.user == request.user

        return False
