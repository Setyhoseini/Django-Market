# core/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsSupport(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and has_group(request.user, "support"))

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and has_group(request.user, "customer"))

class IsContractor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and has_group(request.user, "contractor"))

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "creator", None)
        return bool(
            request.user
            and request.user.is_authenticated
            and (owner == request.user or request.user.is_superuser)
        )
