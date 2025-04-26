import rest_framework.permissions

import business.models


class IsCompanyUser(rest_framework.permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return isinstance(request.user, business.models.Company)


class IsPromoOwner(rest_framework.permissions.BasePermission):
    message = 'The promo code does not belong to this company.'

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'company_id', None) == request.user.id
