"""
Custom Permissions for RBAC
"""
from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """دسترسی فقط برای مدیر"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'


class IsAccountant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'accountant'


class IsStorekeeper(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'storekeeper'


class IsDistributor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'distributor'


class IsStoreOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'store_owner'


class IsManagerOrAccountant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('manager', 'accountant')


class IsManagerOrDistributor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('manager', 'distributor')


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.method in ('GET', 'HEAD', 'OPTIONS')
