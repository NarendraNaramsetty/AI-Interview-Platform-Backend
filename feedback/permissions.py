from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Access Control Policy:
    - Normal candidates can only view/edit their own report card data.
    - Admin/staff members bypass constraints to review all evaluations.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins get full override access
        if request.user.is_staff:
            return True
            
        # Trace ownership checks based on object model attributes
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'evaluation'):
            return obj.evaluation.user == request.user
            
        return False
