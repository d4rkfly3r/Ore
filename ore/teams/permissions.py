from rest_framework import permissions


class OrganizationTeamPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.is_owner_team and request.method == 'DELETE':
            return False  # no, you can't delete the owner team

        return obj.organization.teams.filter(is_owner_team=True, users=request.user).exists()