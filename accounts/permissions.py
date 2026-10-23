from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allows access only to authenticated users whose role is Admin."""

    message = "Only admins can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin_role)