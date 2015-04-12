from rest_framework import permissions

class UserPermission(permissions.BasePermission):
    """
    Allows writes if the target user is the current one
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method in ('DELETE', ):
            return False

        return obj == request.user