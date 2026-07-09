from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission:
    - Allows Admins full access.
    - Allows authenticated owners to read and modify their own objects.
    """
    def has_object_permission(self, request, view, obj):
        # Admin check
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True
            
        # Owner check (assumes obj is UserProfile, UserStatistics, or UserPreference linked to user)
        if hasattr(obj, 'user'):
            return request.user and request.user.is_authenticated and obj.user == request.user
        return request.user and request.user.is_authenticated and obj == request.user


class IsSelf(permissions.BasePermission):
    """
    Allows operations only if requesting user is modifying their own data.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return request.user and request.user.is_authenticated and obj.user == request.user
        return request.user and request.user.is_authenticated and obj == request.user
