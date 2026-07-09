from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` or `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `user` or be the user object itself
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read access to anyone, write access to admin staff only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsSelf(permissions.BasePermission):
    """
    Only allows access if request user matches the target database record.
    """
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and obj == request.user
