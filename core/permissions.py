from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'


class IsContractor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'contractor'


class IsSupport(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'support'


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS or
            obj.creator == request.user or
            request.user.role == 'admin'
        )
