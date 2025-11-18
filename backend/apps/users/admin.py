"""
用户管理后台
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CreatorVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'is_creator', 'is_verified', 'shows_count', 'created_at']
    list_filter = ['is_creator', 'is_verified', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {
            'fields': ('avatar', 'bio', 'is_creator', 'is_verified')
        }),
        ('统计信息', {
            'fields': ('shows_count', 'total_plays')
        }),
    )


@admin.register(CreatorVerification)
class CreatorVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'is_verified', 'attempts', 'verified_at', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'verified_at']
