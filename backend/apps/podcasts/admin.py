"""
播客管理后台
"""
from django.contrib import admin
from .models import Category, Tag, Show, Episode


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color', 'order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'category', 'is_featured', 'episodes_count',
                    'followers_count', 'total_plays', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'created_at']
    search_fields = ['title', 'description', 'creator__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['episodes_count', 'followers_count', 'total_plays', 'created_at', 'updated_at']
    filter_horizontal = ['tags']


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ['title', 'show', 'status', 'duration', 'play_count', 'published_at', 'created_at']
    list_filter = ['status', 'published_at', 'created_at']
    search_fields = ['title', 'description', 'show__title']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['duration', 'file_size', 'play_count', 'like_count', 'comment_count',
                      'created_at', 'updated_at', 'published_at']
    date_hierarchy = 'published_at'
