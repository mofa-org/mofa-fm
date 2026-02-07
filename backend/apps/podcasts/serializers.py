"""
播客序列化器
"""
from django.utils import timezone
from rest_framework import serializers
from apps.users.serializers import UserSerializer
from .models import (
    Category, Tag, Show, Episode, ScriptSession, UploadedReference,
    RSSSource, RSSList, RSSSchedule, RSSRun,
)
from .services.rss_ingest import SCRIPT_TEMPLATE_CHOICES

DEFAULT_SHOW_COVER_URL = '/static/default_show_logo.png'


def _absolute_static_url(request, relative_url: str) -> str:
    if request:
        return request.build_absolute_uri(relative_url)
    return relative_url


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'color', 'order']


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class ShowListSerializer(serializers.ModelSerializer):
    """播客节目/音乐专辑列表序列化器"""

    creator = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Show
        fields = [
            'id', 'title', 'slug', 'description', 'cover', 'cover_url',
            'content_type', 'creator', 'category', 'is_featured',
            'visibility',
            'episodes_count', 'followers_count', 'total_plays',
            'created_at', 'updated_at'
        ]

    def get_cover_url(self, obj):
        if obj.cover:
            return obj.cover.url
        request = self.context.get('request')
        return _absolute_static_url(request, DEFAULT_SHOW_COVER_URL)


class ShowDetailSerializer(serializers.ModelSerializer):
    """播客节目/音乐专辑详情序列化器"""

    creator = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    cover_url = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    shared_with_users = UserSerializer(source='shared_with', many=True, read_only=True)

    class Meta:
        model = Show
        fields = [
            'id', 'title', 'slug', 'description', 'cover', 'cover_url',
            'content_type', 'creator', 'category', 'tags', 'is_featured', 'is_following',
            'visibility', 'shared_with_users',
            'episodes_count', 'followers_count', 'total_plays',
            'created_at', 'updated_at'
        ]

    def get_cover_url(self, obj):
        if obj.cover:
            return obj.cover.url
        request = self.context.get('request')
        return _absolute_static_url(request, DEFAULT_SHOW_COVER_URL)

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from apps.interactions.models import Follow
            return Follow.objects.filter(user=request.user, show=obj).exists()
        return False


class ShowCreateSerializer(serializers.ModelSerializer):
    """创建播客节目/音乐专辑序列化器"""

    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    shared_with_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Show
        fields = [
            'title', 'description', 'cover', 'content_type',
            'visibility', 'category_id', 'tag_ids', 'shared_with_ids'
        ]
        extra_kwargs = {
            'cover': {'required': False},
            'description': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', [])
        shared_with_ids = validated_data.pop('shared_with_ids', [])

        # 设置创作者
        validated_data['creator'] = self.context['request'].user
        if 'description' not in validated_data:
            validated_data['description'] = ''

        # 设置分类
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                validated_data['category'] = category
            except Category.DoesNotExist:
                pass

        show = Show.objects.create(**validated_data)

        # 设置标签
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            show.tags.set(tags)

        # 设置共享用户
        if shared_with_ids:
            from apps.users.models import User
            users = User.objects.filter(id__in=shared_with_ids)
            show.shared_with.set(users)

        return show

    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', None)
        shared_with_ids = validated_data.pop('shared_with_ids', None)

        # 如果 category_id 存在但为 None，则清除分类
        if 'category_id' in self.initial_data:
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    instance.category = category
                except Category.DoesNotExist:
                    pass
            else:
                instance.category = None

        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 更新标签
        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)

        # 更新共享用户
        if shared_with_ids is not None:
            from apps.users.models import User
            users = User.objects.filter(id__in=shared_with_ids)
            instance.shared_with.set(users)

        return instance


class EpisodeListSerializer(serializers.ModelSerializer):
    """单集/单曲列表序列化器"""

    show = ShowListSerializer(read_only=True)
    audio_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = [
            'id', 'title', 'slug', 'description', 'cover', 'cover_url',
            'show', 'audio_file', 'audio_url', 'duration', 'file_size',
            'episode_number', 'season_number',
            'artist', 'genre', 'album_name', 'release_date',
            'visibility',
            'status', 'generation_stage', 'generation_error', 'generation_meta',
            'play_count', 'like_count', 'comment_count',
            'published_at', 'created_at'
        ]

    def get_audio_url(self, obj):
        if obj.audio_file:
            return obj.audio_file.url
        return None

    def get_cover_url(self, obj):
        if obj.cover:
            return obj.cover.url
        elif obj.show and obj.show.cover:
            return obj.show.cover.url
        request = self.context.get('request')
        return _absolute_static_url(request, DEFAULT_SHOW_COVER_URL)


class EpisodeDetailSerializer(serializers.ModelSerializer):
    """单集/单曲详情序列化器"""

    show = ShowDetailSerializer(read_only=True)
    audio_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    play_position = serializers.SerializerMethodField()
    shared_with_users = UserSerializer(source='shared_with', many=True, read_only=True)

    class Meta:
        model = Episode
        fields = [
            'id', 'title', 'slug', 'description', 'cover', 'cover_url',
            'show', 'audio_file', 'audio_url', 'duration', 'file_size',
            'episode_number', 'season_number',
            'artist', 'genre', 'album_name', 'release_date',
            'visibility', 'shared_with_users',
            'status', 'generation_stage', 'generation_error', 'generation_meta',
            'play_count', 'like_count', 'comment_count',
            'is_liked', 'play_position',
            'script',  # 添加脚本字段
            'mode', 'dialogue', 'participants_config',  # Debate/Conference字段
            'published_at', 'created_at', 'updated_at'
        ]

    def get_audio_url(self, obj):
        if obj.audio_file:
            return obj.audio_file.url
        return None

    def get_cover_url(self, obj):
        if obj.cover:
            return obj.cover.url
        elif obj.show and obj.show.cover:
            return obj.show.cover.url
        request = self.context.get('request')
        return _absolute_static_url(request, DEFAULT_SHOW_COVER_URL)

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from apps.interactions.models import Like
            return Like.objects.filter(user=request.user, episode=obj).exists()
        return False

    def get_play_position(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from apps.interactions.models import PlayHistory
            try:
                history = PlayHistory.objects.get(user=request.user, episode=obj)
                return history.position
            except PlayHistory.DoesNotExist:
                pass
        return 0


class EpisodeCreateSerializer(serializers.ModelSerializer):
    """创建单集/单曲序列化器"""

    show_id = serializers.IntegerField(required=False, allow_null=True)
    audio_file = serializers.FileField(required=False)
    shared_with_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Episode
        fields = [
            'show_id', 'title', 'description', 'cover',
            'audio_file', 'episode_number', 'season_number',
            'artist', 'genre', 'album_name', 'release_date',
            'visibility', 'shared_with_ids'
        ]

    def validate_show_id(self, value):
        """验证播客节目归属"""
        if not value:
            return value
        user = self.context['request'].user
        try:
            show = Show.objects.get(id=value, creator=user)
            return value
        except Show.DoesNotExist:
            raise serializers.ValidationError("节目不存在或您没有权限")

    def validate(self, attrs):
        """验证数据"""
        # 创建时必须提供音频
        if not self.instance:
            if 'audio_file' not in attrs:
                raise serializers.ValidationError({'audio_file': '创建单集时必须上传音频文件'})
        return attrs

    def create(self, validated_data):
        show_id = validated_data.pop('show_id', None)
        shared_with_ids = validated_data.pop('shared_with_ids', [])

        if show_id:
            show = Show.objects.get(id=show_id)
        else:
            from .services.default_show import get_or_create_default_show
            show, _ = get_or_create_default_show(self.context['request'].user)
        validated_data['show'] = show
        validated_data['status'] = 'processing'

        episode = Episode.objects.create(**validated_data)

        # 设置共享用户
        if shared_with_ids:
            from apps.users.models import User
            users = User.objects.filter(id__in=shared_with_ids)
            episode.shared_with.set(users)

        # 触发音频处理任务
        from .tasks import process_episode_audio
        process_episode_audio.delay(episode.id)

        return episode

    def update(self, instance, validated_data):
        """更新单集"""
        # 移除 show_id，不允许更新所属节目
        validated_data.pop('show_id', None)

        # 如果有新的音频文件，设置状态为处理中
        if 'audio_file' in validated_data and validated_data['audio_file']:
            instance.status = 'processing'

        # 更新字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # 如果有新音频，触发处理任务
        if 'audio_file' in validated_data and validated_data['audio_file']:
            from .tasks import process_episode_audio
            process_episode_audio.delay(instance.id)

        return instance


class PodcastGenerationSerializer(serializers.Serializer):
    """播客生成请求序列化器"""

    title = serializers.CharField(max_length=255, required=True)
    show_id = serializers.IntegerField(required=False, allow_null=True)
    script = serializers.CharField(required=True, style={'base_template': 'textarea.html'})
    host_name = serializers.CharField(required=False, allow_blank=True, max_length=64)
    guest_name = serializers.CharField(required=False, allow_blank=True, max_length=64)
    host_voice_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    guest_voice_id = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_show_id(self, value):
        if not value:
            return value
        user = self.context['request'].user
        try:
            show = Show.objects.get(id=value, creator=user)
            return value
        except Show.DoesNotExist:
            raise serializers.ValidationError("节目不存在或您没有权限")


class RSSPodcastGenerationSerializer(serializers.Serializer):
    """RSS 播客生成请求"""

    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    show_id = serializers.IntegerField(required=False, allow_null=True)
    rss_url = serializers.URLField(required=False, allow_blank=True)
    rss_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        allow_empty=False
    )
    template = serializers.ChoiceField(required=False, choices=SCRIPT_TEMPLATE_CHOICES, default='news_flash')
    deduplicate = serializers.BooleanField(required=False, default=True)
    sort_by = serializers.ChoiceField(
        required=False,
        choices=[('latest', 'latest'), ('oldest', 'oldest'), ('title', 'title')],
        default='latest'
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    max_items = serializers.IntegerField(required=False, min_value=1, max_value=20, default=8)
    dry_run = serializers.BooleanField(required=False, default=False)
    script = serializers.CharField(required=False, allow_blank=True, style={'base_template': 'textarea.html'})
    host_name = serializers.CharField(required=False, allow_blank=True, max_length=64)
    guest_name = serializers.CharField(required=False, allow_blank=True, max_length=64)
    host_voice_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    guest_voice_id = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_show_id(self, value):
        if not value:
            return value
        user = self.context['request'].user
        try:
            Show.objects.get(id=value, creator=user)
            return value
        except Show.DoesNotExist:
            raise serializers.ValidationError("节目不存在或您没有权限")

    def validate(self, attrs):
        rss_urls = list(attrs.get('rss_urls') or [])
        rss_url = (attrs.get('rss_url') or '').strip()
        if rss_url:
            rss_urls.insert(0, rss_url)

        # 归一化并去空
        normalized_urls = []
        for url in rss_urls:
            value = (url or '').strip()
            if value:
                normalized_urls.append(value)
        if not normalized_urls:
            raise serializers.ValidationError({'rss_url': '请至少提供一个 RSS 地址'})

        attrs['rss_urls'] = normalized_urls
        attrs['rss_url'] = normalized_urls[0]

        scheduled_at = attrs.get('scheduled_at')
        if scheduled_at and scheduled_at <= timezone.now():
            raise serializers.ValidationError({'scheduled_at': '定时任务时间需晚于当前时间'})
        return attrs


class SourcePodcastGenerationSerializer(serializers.Serializer):
    """链接源（RSS/网页）播客生成请求"""

    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    show_id = serializers.IntegerField(required=False, allow_null=True)
    source_url = serializers.URLField(required=True)
    template = serializers.ChoiceField(required=False, choices=SCRIPT_TEMPLATE_CHOICES, default='news_flash')
    max_items = serializers.IntegerField(required=False, min_value=1, max_value=20, default=8)
    dry_run = serializers.BooleanField(required=False, default=False)
    host_name = serializers.CharField(required=False, allow_blank=True, max_length=64)
    guest_name = serializers.CharField(required=False, allow_blank=True, max_length=64)
    host_voice_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
    guest_voice_id = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_show_id(self, value):
        if not value:
            return value
        user = self.context['request'].user
        try:
            Show.objects.get(id=value, creator=user)
            return value
        except Show.DoesNotExist:
            raise serializers.ValidationError("节目不存在或您没有权限")


class RSSSourceSerializer(serializers.ModelSerializer):
    """RSS 源"""

    class Meta:
        model = RSSSource
        fields = [
            'id', 'name', 'url', 'description', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_url(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return value
        qs = RSSSource.objects.filter(creator=user, url=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError('该 RSS 地址已存在')
        return value


class RSSListSerializer(serializers.ModelSerializer):
    """RSS 列表"""

    sources = RSSSourceSerializer(many=True, read_only=True)
    source_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    source_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RSSList
        fields = [
            'id', 'name', 'description', 'is_active',
            'sources', 'source_ids', 'source_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_source_count(self, obj):
        return obj.sources.count()

    def validate_source_ids(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return []
        ids = list(dict.fromkeys(value or []))
        if not ids:
            return []
        sources = RSSSource.objects.filter(creator=user, id__in=ids)
        if sources.count() != len(ids):
            raise serializers.ValidationError('source_ids 含无效或无权限的源')
        return ids

    def create(self, validated_data):
        source_ids = validated_data.pop('source_ids', [])
        validated_data['creator'] = self.context['request'].user
        instance = RSSList.objects.create(**validated_data)
        if source_ids:
            instance.sources.set(
                RSSSource.objects.filter(creator=instance.creator, id__in=source_ids)
            )
        return instance

    def update(self, instance, validated_data):
        source_ids = validated_data.pop('source_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if source_ids is not None:
            instance.sources.set(
                RSSSource.objects.filter(creator=instance.creator, id__in=source_ids)
            )
        return instance


class RSSScheduleSerializer(serializers.ModelSerializer):
    """RSS 定时规则"""

    rss_list = RSSListSerializer(read_only=True)
    rss_list_id = serializers.IntegerField(write_only=True)
    show = ShowListSerializer(read_only=True)
    show_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    week_days = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        required=False,
        allow_empty=True,
    )
    template = serializers.ChoiceField(required=False, choices=SCRIPT_TEMPLATE_CHOICES, default='news_flash')

    class Meta:
        model = RSSSchedule
        fields = [
            'id', 'name',
            'rss_list', 'rss_list_id',
            'show', 'show_id',
            'template', 'max_items', 'deduplicate', 'sort_by',
            'host_name', 'guest_name', 'host_voice_id', 'guest_voice_id',
            'timezone_name', 'run_time', 'frequency', 'week_days',
            'is_active',
            'next_run_at', 'last_run_at', 'last_status', 'last_error',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'next_run_at', 'last_run_at', 'last_status', 'last_error',
            'created_at', 'updated_at',
        ]

    def validate_rss_list_id(self, value):
        user = self.context['request'].user
        try:
            RSSList.objects.get(id=value, creator=user)
        except RSSList.DoesNotExist:
            raise serializers.ValidationError('RSS 列表不存在或无权限')
        return value

    def validate_show_id(self, value):
        if not value:
            return value
        user = self.context['request'].user
        try:
            Show.objects.get(id=value, creator=user)
        except Show.DoesNotExist:
            raise serializers.ValidationError('节目不存在或无权限')
        return value

    def validate_week_days(self, value):
        result = sorted(list(dict.fromkeys(value or [])))
        return result

    def validate(self, attrs):
        frequency = attrs.get('frequency') or getattr(self.instance, 'frequency', 'daily')
        week_days = attrs.get('week_days')
        if week_days is None and self.instance is not None:
            week_days = self.instance.week_days
        if frequency == 'weekly' and not week_days:
            raise serializers.ValidationError({'week_days': '每周模式请至少选择一天'})
        return attrs

    def create(self, validated_data):
        rss_list_id = validated_data.pop('rss_list_id')
        show_id = validated_data.pop('show_id', None)
        validated_data['creator'] = self.context['request'].user
        validated_data['rss_list'] = RSSList.objects.get(id=rss_list_id, creator=validated_data['creator'])
        if show_id:
            validated_data['show'] = Show.objects.get(id=show_id, creator=validated_data['creator'])
        return RSSSchedule.objects.create(**validated_data)

    def update(self, instance, validated_data):
        rss_list_id = validated_data.pop('rss_list_id', None)
        show_id = validated_data.pop('show_id', None) if 'show_id' in validated_data else None

        if rss_list_id is not None:
            instance.rss_list = RSSList.objects.get(id=rss_list_id, creator=instance.creator)
        if 'show_id' in self.initial_data:
            instance.show = (
                Show.objects.get(id=show_id, creator=instance.creator)
                if show_id else None
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RSSRunSerializer(serializers.ModelSerializer):
    """RSS 运行记录"""

    schedule_name = serializers.SerializerMethodField()
    episode_title = serializers.SerializerMethodField()

    class Meta:
        model = RSSRun
        fields = [
            'id', 'schedule', 'schedule_name',
            'episode', 'episode_title',
            'status', 'trigger_type', 'message', 'error',
            'item_count', 'meta',
            'started_at', 'finished_at',
        ]

    def get_schedule_name(self, obj):
        return obj.schedule.name if obj.schedule_id else ''

    def get_episode_title(self, obj):
        return obj.episode.title if obj.episode_id else ''


class UploadedReferenceSerializer(serializers.ModelSerializer):
    """上传的参考文件序列化器"""

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedReference
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'file_url', 'extracted_text', 'uploaded_at'
        ]
        read_only_fields = ['extracted_text', 'uploaded_at']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class ScriptSessionSerializer(serializers.ModelSerializer):
    """脚本会话序列化器"""

    creator = UserSerializer(read_only=True)
    show = ShowListSerializer(read_only=True)
    uploaded_files = UploadedReferenceSerializer(many=True, read_only=True)
    uploaded_files_count = serializers.SerializerMethodField()

    class Meta:
        model = ScriptSession
        fields = [
            'id', 'title', 'status', 'creator', 'show',
            'chat_history', 'current_script', 'script_versions',
            'voice_config', 'uploaded_files', 'uploaded_files_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['creator', 'chat_history', 'script_versions', 'created_at', 'updated_at']

    def get_uploaded_files_count(self, obj):
        return obj.uploaded_files.count()


class ScriptChatSerializer(serializers.Serializer):
    """脚本对话请求序列化器"""

    message = serializers.CharField(required=True, help_text="用户消息")


class ScriptSessionCreateSerializer(serializers.ModelSerializer):
    """创建脚本会话序列化器"""

    show_id = serializers.IntegerField(required=False, allow_null=True, help_text="关联的节目ID（可选）")

    class Meta:
        model = ScriptSession
        fields = ['title', 'show_id']

    def validate_show_id(self, value):
        if value:
            user = self.context['request'].user
            try:
                Show.objects.get(id=value, creator=user)
                return value
            except Show.DoesNotExist:
                raise serializers.ValidationError("节目不存在或您没有权限")
        return value

    def create(self, validated_data):
        show_id = validated_data.pop('show_id', None)
        validated_data['creator'] = self.context['request'].user

        if show_id:
            validated_data['show_id'] = show_id

        return ScriptSession.objects.create(**validated_data)
