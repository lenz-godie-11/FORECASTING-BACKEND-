from rest_framework.permissions import BasePermission

from src.auth.roles import STAFF_ROLES


class IsStaff(BasePermission):
    """Allow only authenticated users holding an ADMIN or MANAGER role."""

    message = "Authentication with an ADMIN or MANAGER account is required."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.groups.filter(name__in=STAFF_ROLES).exists()
        )
