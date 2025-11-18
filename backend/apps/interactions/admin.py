"""
互动管理后台
"""
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Follow, Like, PlayHistory, Comment


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['user', 'show', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'show__title']
    date_hierarchy = 'created_at'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'episode', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'episode__title']
    date_hierarchy = 'created_at'


@admin.register(PlayHistory)
class PlayHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'episode', 'position', 'completed', 'last_played_at', 'created_at']
    list_filter = ['completed', 'last_played_at']
    search_fields = ['user__username', 'episode__title']
    date_hierarchy = 'last_played_at'


@admin.register(Comment)
class CommentAdmin(MPTTModelAdmin):
    list_display = ['user', 'episode', 'text_preview', 'timestamp', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'episode__title', 'text']
    date_hierarchy = 'created_at'

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = '内容预览'
