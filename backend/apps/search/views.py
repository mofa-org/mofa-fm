"""
搜索视图
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from apps.podcasts.models import Show, Episode
from apps.podcasts.serializers import ShowListSerializer, EpisodeListSerializer
from apps.interactions.models import Comment
from apps.interactions.serializers import CommentSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):
    """
    全局搜索
    搜索范围：播客标题、单集标题、评论内容
    """
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return Response({
            'shows': [],
            'episodes': [],
            'comments': [],
            'total': 0
        })

    # 搜索播客节目
    shows = Show.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_active=True
    ).select_related('creator', 'category')[:10]

    # 搜索单集
    episodes = Episode.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        status='published'
    ).select_related('show__creator')[:20]

    # 搜索评论
    comments = Comment.objects.filter(
        text__icontains=query,
        episode__status='published'
    ).select_related('user', 'episode', 'episode__show')[:10]

    return Response({
        'shows': ShowListSerializer(shows, many=True, context={'request': request}).data,
        'episodes': EpisodeListSerializer(episodes, many=True, context={'request': request}).data,
        'comments': CommentSerializer(comments, many=True).data,
        'total': len(shows) + len(episodes) + len(comments)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def quick_search(request):
    """
    快速搜索（仅标题）
    用于搜索建议/自动完成
    """
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return Response({'results': []})

    # 搜索播客和单集标题
    shows = Show.objects.filter(
        title__icontains=query,
        is_active=True
    ).values('id', 'title', 'slug')[:5]

    episodes = Episode.objects.filter(
        title__icontains=query,
        status='published'
    ).select_related('show').values('id', 'title', 'slug', 'show__title', 'show__slug')[:10]

    results = []

    # 播客节目结果
    for show in shows:
        results.append({
            'type': 'show',
            'id': show['id'],
            'title': show['title'],
            'slug': show['slug']
        })

    # 单集结果
    for episode in episodes:
        results.append({
            'type': 'episode',
            'id': episode['id'],
            'title': episode['title'],
            'slug': episode['slug'],
            'show_title': episode['show__title'],
            'show_slug': episode['show__slug']
        })

    return Response({'results': results})
