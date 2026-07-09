from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows admins to perform CRUD writes, while letting authenticated users read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAdminUserOnly(permissions.BasePermission):
    """
    Strictly restricts access to Django administrators (is_staff=True).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff
