from rest_framework import permissions

class ProjectPermission(permissions.BasePermission):
    """
    Allows writes if the user has permission
    """

    method_map = {
        'POST': 'project.create',
        'DELETE': 'project.delete',
    }

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated()

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # PUT and PATCH are guarded by the serializer
        if request.method in ('PUT', 'PATCH'):
            return True

        if request.method not in self.method_map:
            return False  # fail safe

        return obj.user_has_permission(request.user, self.method_map[request.method])
