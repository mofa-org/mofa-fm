"""
播客权限
"""
from rest_framework import permissions


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    只有创作者可以创建内容
    所有人可以读取
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_creator


class IsShowOwner(permissions.BasePermission):
    """
    只有节目所有者可以编辑/删除
    """

    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user
