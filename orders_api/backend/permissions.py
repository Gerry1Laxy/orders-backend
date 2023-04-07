from rest_framework.permissions import BasePermission

class IsShop(BasePermission):
    def has_permission(self, request, view):
        return request.user.type == 'shop'

