from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Access policy:
    - Standard authenticated candidates get read-only (GET, HEAD, OPTIONS) access.
    - Administrative staff members (is_staff=True) get full CRUD capability.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            # Safe methods (GET, HEAD, OPTIONS) are allowed for any user
            if request.method in permissions.SAFE_METHODS:
                return True
            # Write methods (POST, PUT, PATCH, DELETE) require admin staff privileges
            return request.user.is_staff
        return False
