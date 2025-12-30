from rest_framework import permissions

class IsEmailVerified(permissions.BasePermission):
    """
    允许仅当用户的邮箱已验证时访问
    """
    message = '您的邮箱尚未验证，请先验证邮箱。'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.email_verified)
