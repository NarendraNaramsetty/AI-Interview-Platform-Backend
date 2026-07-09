from rest_framework import permissions

class IsInterviewOwnerOrAdmin(permissions.BasePermission):
    """
    Restricts access to InterviewSessions:
    - Staff administrators can access and view all sessions.
    - Authenticated owners can view, update, or manipulate their own sessions.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            if request.user.is_staff:
                return True
            return obj.user == request.user
        return False
