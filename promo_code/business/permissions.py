import rest_framework.permissions

import business.models


class IsCompanyUser(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, business.models.Company)
