import rest_framework.permissions


class IsOwnerOrReadOnly(rest_framework.permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    Read-only for others.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in rest_framework.permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
