from rest_framework import permissions

class IsResumeOwnerOrAdmin(permissions.BasePermission):
    """
    Restricts access to Resumes:
    - Admins (staff) can view and modify all records.
    - Authenticated users can view/modify only their own uploaded resumes.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            if request.user.is_staff:
                return True
            return obj.user == request.user
        return False
