"""
搜索管理后台
"""
from django.contrib import admin
from .models import SearchHistory, PopularSearch


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'session_key', 'results_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query', 'user__username']
    readonly_fields = ['user', 'query', 'session_key', 'results_count', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        # 搜索历史只能通过系统自动创建
        return False


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    list_display = ['query', 'search_count', 'last_searched_at', 'created_at']
    list_filter = ['last_searched_at', 'created_at']
    search_fields = ['query']
    readonly_fields = ['search_count', 'last_searched_at', 'created_at']
    ordering = ['-search_count', '-last_searched_at']

    def has_add_permission(self, request):
        # 热门搜索只能通过系统自动创建
        return False
