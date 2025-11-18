"""
互动序列化器
"""
from rest_framework import serializers
from apps.users.serializers import UserSerializer
from .models import Follow, Like, PlayHistory, Comment


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""

    user = UserSerializer(read_only=True)
    children = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'episode', 'user', 'parent', 'text', 'timestamp',
            'children', 'reply_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_children(self, obj):
        """获取子评论"""
        if obj.get_children().exists():
            return CommentSerializer(obj.get_children(), many=True).data
        return []

    def get_reply_count(self, obj):
        """获取回复数"""
        return obj.get_descendant_count()


class CommentCreateSerializer(serializers.ModelSerializer):
    """创建评论序列化器"""

    class Meta:
        model = Comment
        fields = ['episode', 'parent', 'text', 'timestamp']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        comment = Comment.objects.create(**validated_data)

        # 更新单集评论数
        episode = comment.episode
        episode.comment_count = episode.comments.count()
        episode.save()

        return comment


class PlayHistorySerializer(serializers.ModelSerializer):
    """播放历史序列化器"""

    from apps.podcasts.serializers import EpisodeListSerializer
    episode = EpisodeListSerializer(read_only=True)

    class Meta:
        model = PlayHistory
        fields = ['id', 'episode', 'position', 'completed', 'last_played_at', 'created_at']


class UpdatePlayProgressSerializer(serializers.Serializer):
    """更新播放进度序列化器"""

    episode_id = serializers.IntegerField(required=True)
    position = serializers.IntegerField(required=True, min_value=0)
    duration = serializers.IntegerField(required=False)


class FollowSerializer(serializers.ModelSerializer):
    """关注序列化器"""

    from apps.podcasts.serializers import ShowListSerializer
    show = ShowListSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'show', 'created_at']
