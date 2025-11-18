"""
互动视图
"""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.podcasts.models import Show, Episode
from .models import Follow, Like, PlayHistory, Comment
from .serializers import (
    CommentSerializer, CommentCreateSerializer,
    PlayHistorySerializer, UpdatePlayProgressSerializer,
    FollowSerializer
)


# 评论

class CommentListView(generics.ListAPIView):
    """评论列表"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        episode_id = self.kwargs.get('episode_id')
        # 只获取顶级评论，子评论通过序列化器递归获取
        return Comment.objects.filter(
            episode_id=episode_id,
            parent__isnull=True
        ).select_related('user').order_by('-created_at')


class CommentCreateView(generics.CreateAPIView):
    """创建评论"""
    serializer_class = CommentCreateSerializer
    permission_classes = [IsAuthenticated]


class CommentDeleteView(generics.DestroyAPIView):
    """删除评论"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(user=self.request.user)


# 点赞

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, episode_id):
    """切换点赞状态"""
    episode = get_object_or_404(Episode, id=episode_id, status='published')
    user = request.user

    like, created = Like.objects.get_or_create(user=user, episode=episode)

    if created:
        # 新增点赞
        episode.like_count += 1
        episode.save()
        return Response({'liked': True, 'like_count': episode.like_count})
    else:
        # 取消点赞
        like.delete()
        episode.like_count = max(0, episode.like_count - 1)
        episode.save()
        return Response({'liked': False, 'like_count': episode.like_count})


# 关注

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_follow(request, show_id):
    """切换关注状态"""
    show = get_object_or_404(Show, id=show_id, is_active=True)
    user = request.user

    follow, created = Follow.objects.get_or_create(user=user, show=show)

    if created:
        # 新增关注
        show.followers_count += 1
        show.save()
        return Response({'following': True, 'followers_count': show.followers_count})
    else:
        # 取消关注
        follow.delete()
        show.followers_count = max(0, show.followers_count - 1)
        show.save()
        return Response({'following': False, 'followers_count': show.followers_count})


class MyFollowingView(generics.ListAPIView):
    """我的关注列表"""
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user).select_related('show').order_by('-created_at')


# 播放历史

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_play_progress(request):
    """更新播放进度"""
    serializer = UpdatePlayProgressSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    episode_id = serializer.validated_data['episode_id']
    position = serializer.validated_data['position']
    duration = serializer.validated_data.get('duration')

    episode = get_object_or_404(Episode, id=episode_id, status='published')
    user = request.user

    # 获取或创建播放历史
    history, created = PlayHistory.objects.get_or_create(
        user=user,
        episode=episode
    )

    # 更新进度
    history.position = position

    # 判断是否已完成（播放到90%以上视为完成）
    if duration and position >= duration * 0.9:
        history.completed = True

    history.save()

    # 更新播放次数（首次播放）
    if created:
        episode.play_count += 1
        episode.save()

        # 更新节目总播放数
        show = episode.show
        show.total_plays += 1
        show.save()

    return Response({
        'success': True,
        'position': history.position,
        'completed': history.completed
    })


class MyPlayHistoryView(generics.ListAPIView):
    """我的播放历史"""
    serializer_class = PlayHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlayHistory.objects.filter(
            user=self.request.user
        ).select_related('episode__show').order_by('-last_played_at')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def continue_listening(request):
    """继续收听（最近未完成的单集）"""
    history = PlayHistory.objects.filter(
        user=request.user,
        completed=False,
        position__gt=0
    ).select_related('episode__show').order_by('-last_played_at').first()

    if history:
        serializer = PlayHistorySerializer(history)
        return Response(serializer.data)

    return Response({'message': '没有未完成的单集'}, status=status.HTTP_404_NOT_FOUND)
