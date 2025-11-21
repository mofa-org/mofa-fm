"""
播客序列化器
"""
from rest_framework import serializers
from apps.users.serializers import UserSerializer
from .models import Category, Tag, Show, Episode, ScriptSession, UploadedReference


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
            'episodes_count', 'followers_count', 'total_plays',
            'created_at', 'updated_at'
        ]

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover:
            if request:
                return request.build_absolute_uri(obj.cover.url)
            return obj.cover.url
        return None


class ShowDetailSerializer(serializers.ModelSerializer):
    """播客节目/音乐专辑详情序列化器"""

    creator = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    cover_url = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = Show
        fields = [
            'id', 'title', 'slug', 'description', 'cover', 'cover_url',
            'content_type', 'creator', 'category', 'tags', 'is_featured', 'is_following',
            'episodes_count', 'followers_count', 'total_plays',
            'created_at', 'updated_at'
        ]

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover:
            if request:
                return request.build_absolute_uri(obj.cover.url)
            return obj.cover.url
        return None

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

    class Meta:
        model = Show
        fields = ['title', 'description', 'cover', 'content_type', 'category_id', 'tag_ids']

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', [])

        # 设置创作者
        validated_data['creator'] = self.context['request'].user

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

        return show


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
            'status', 'play_count', 'like_count', 'comment_count',
            'published_at', 'created_at'
        ]

    def get_audio_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file:
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover:
            if request:
                return request.build_absolute_uri(obj.cover.url)
        elif obj.show.cover:
            if request:
                return request.build_absolute_uri(obj.show.cover.url)
            return obj.show.cover.url
        return None


class EpisodeDetailSerializer(serializers.ModelSerializer):
    """单集/单曲详情序列化器"""

    show = ShowDetailSerializer(read_only=True)
    audio_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    play_position = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = [
            'id', 'title', 'slug', 'description', 'cover', 'cover_url',
            'show', 'audio_file', 'audio_url', 'duration', 'file_size',
            'episode_number', 'season_number',
            'artist', 'genre', 'album_name', 'release_date',
            'status', 'play_count', 'like_count', 'comment_count',
            'is_liked', 'play_position',
            'published_at', 'created_at', 'updated_at'
        ]

    def get_audio_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file:
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover:
            if request:
                return request.build_absolute_uri(obj.cover.url)
        elif obj.show.cover:
            if request:
                return request.build_absolute_uri(obj.show.cover.url)
            return obj.show.cover.url
        return None

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

    show_id = serializers.IntegerField(required=False)
    audio_file = serializers.FileField(required=False)

    class Meta:
        model = Episode
        fields = [
            'show_id', 'title', 'description', 'cover',
            'audio_file', 'episode_number', 'season_number',
            'artist', 'genre', 'album_name', 'release_date'
        ]

    def validate_show_id(self, value):
        """验证播客节目归属"""
        user = self.context['request'].user
        try:
            show = Show.objects.get(id=value, creator=user)
            return value
        except Show.DoesNotExist:
            raise serializers.ValidationError("节目不存在或您没有权限")

    def validate(self, attrs):
        """验证数据"""
        # 创建时必须提供 show_id 和 audio_file
        if not self.instance:
            if 'show_id' not in attrs:
                raise serializers.ValidationError({'show_id': '创建单集时必须指定所属节目'})
            if 'audio_file' not in attrs:
                raise serializers.ValidationError({'audio_file': '创建单集时必须上传音频文件'})
        return attrs

    def create(self, validated_data):
        show_id = validated_data.pop('show_id')
        show = Show.objects.get(id=show_id)
        validated_data['show'] = show
        validated_data['status'] = 'processing'

        episode = Episode.objects.create(**validated_data)

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
    show_id = serializers.IntegerField(required=True)
    script = serializers.CharField(required=True, style={'base_template': 'textarea.html'})

    def validate_show_id(self, value):
        user = self.context['request'].user
        try:
            show = Show.objects.get(id=value, creator=user)
            return value
        except Show.DoesNotExist:
            raise serializers.ValidationError("节目不存在或您没有权限")


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
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
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
