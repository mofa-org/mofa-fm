"""
播客管理后台
"""
from django.contrib import admin
from .models import Category, Tag, Show, Episode, ScriptSession, UploadedReference


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
    list_display = ['title', 'creator', 'category', 'content_type', 'visibility', 'is_featured',
                    'is_active', 'episodes_count', 'followers_count', 'total_plays', 'created_at']
    list_filter = ['is_active', 'is_featured', 'content_type', 'visibility', 'category', 'created_at']
    search_fields = ['title', 'description', 'creator__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['episodes_count', 'followers_count', 'total_plays', 'created_at', 'updated_at']
    filter_horizontal = ['tags', 'shared_with']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'slug', 'description', 'cover', 'content_type', 'creator')
        }),
        ('分类标签', {
            'fields': ('category', 'tags')
        }),
        ('可见性控制', {
            'fields': ('visibility', 'shared_with')
        }),
        ('状态', {
            'fields': ('is_active', 'is_featured')
        }),
        ('统计信息', {
            'fields': ('episodes_count', 'followers_count', 'total_plays'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ['title', 'show', 'status', 'visibility', 'duration_display', 'play_count',
                    'like_count', 'comment_count', 'published_at']
    list_filter = ['status', 'visibility', 'show__content_type', 'published_at', 'created_at']
    search_fields = ['title', 'description', 'show__title', 'artist', 'album_name']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['duration', 'file_size', 'play_count', 'like_count', 'comment_count',
                      'created_at', 'updated_at', 'published_at', 'audio_url', 'cover_url']
    filter_horizontal = ['shared_with']
    date_hierarchy = 'published_at'

    fieldsets = (
        ('基本信息', {
            'fields': ('show', 'title', 'slug', 'description', 'cover')
        }),
        ('音频文件', {
            'fields': ('audio_file', 'audio_url', 'duration', 'file_size')
        }),
        ('播客元数据', {
            'fields': ('episode_number', 'season_number'),
            'classes': ('collapse',)
        }),
        ('音乐元数据', {
            'fields': ('artist', 'genre', 'album_name', 'release_date'),
            'classes': ('collapse',)
        }),
        ('可见性控制', {
            'fields': ('visibility', 'shared_with')
        }),
        ('状态', {
            'fields': ('status', 'published_at')
        }),
        ('统计信息', {
            'fields': ('play_count', 'like_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def duration_display(self, obj):
        """格式化显示时长"""
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}:{seconds:02d}"
        return "-"
    duration_display.short_description = '时长'


class UploadedReferenceInline(admin.TabularInline):
    """脚本会话的参考文件内联显示"""
    model = UploadedReference
    extra = 0
    readonly_fields = ['original_filename', 'file_type', 'file_size', 'uploaded_at']
    fields = ['original_filename', 'file_type', 'file_size', 'uploaded_at']
    can_delete = True


@admin.register(ScriptSession)
class ScriptSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'creator', 'show', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'creator__username', 'show__title']
    readonly_fields = ['creator', 'chat_history', 'script_versions', 'created_at', 'updated_at']
    inlines = [UploadedReferenceInline]

    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'creator', 'show', 'status')
        }),
        ('脚本内容', {
            'fields': ('current_script', 'script_versions')
        }),
        ('对话历史', {
            'fields': ('chat_history',),
            'classes': ('collapse',)
        }),
        ('音色配置', {
            'fields': ('voice_config',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(UploadedReference)
class UploadedReferenceAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'session', 'file_type', 'file_size', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['original_filename', 'session__title']
    readonly_fields = ['extracted_text', 'uploaded_at']
