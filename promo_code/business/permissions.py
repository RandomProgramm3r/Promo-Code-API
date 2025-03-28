import business.models
import rest_framework.permissions


class IsCompanyUser(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, business.models.Company)
