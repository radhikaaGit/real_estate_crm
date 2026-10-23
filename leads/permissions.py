from rest_framework.permissions import BasePermission


class IsAdminOrAssignedEmployee(BasePermission):
    """
    Object-level permission.
    - Admin: any lead.
    - Sales employee: only a lead currently assigned to them.
    """

    message = "You do not have permission to access this lead."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role:
            return True
        return obj.assigned_to_id == user.id