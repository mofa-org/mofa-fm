"""
搜索视图
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F, Count, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from apps.podcasts.models import Show, Episode
from apps.podcasts.serializers import ShowListSerializer, EpisodeListSerializer
from apps.interactions.models import Comment
from apps.interactions.serializers import CommentSerializer
from .models import SearchHistory, PopularSearch


class SearchResultsPagination(PageNumberPagination):
    """搜索结果分页"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def _record_search(query, results_count, user=None, session_key=None):
    """记录搜索历史和热门搜索"""
    # 记录搜索历史
    SearchHistory.objects.create(
        query=query,
        results_count=results_count,
        user=user,
        session_key=session_key
    )

    # 更新热门搜索
    popular, created = PopularSearch.objects.get_or_create(
        query=query,
        defaults={'search_count': 1}
    )
    if not created:
        popular.search_count = F('search_count') + 1
        popular.save(update_fields=['search_count', 'last_searched_at'])


def _calculate_relevance_score(obj, query):
    """计算相关度分数"""
    score = 0
    query_lower = query.lower()

    # 标题完全匹配
    if hasattr(obj, 'title') and obj.title.lower() == query_lower:
        score += 100
    # 标题包含
    elif hasattr(obj, 'title') and query_lower in obj.title.lower():
        score += 50

    # 描述包含
    if hasattr(obj, 'description') and obj.description and query_lower in obj.description.lower():
        score += 20

    # 播放量加成（针对 Episode 和 Show）
    if hasattr(obj, 'play_count'):
        score += min(obj.play_count // 100, 30)  # 最多加30分

    return score


@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):
    """
    全局搜索
    支持高级过滤和排序

    参数:
    - q: 搜索关键词
    - type: 结果类型 (show/episode/comment/all)
    - category: 分类 ID
    - tag: 标签 ID
    - date_from: 开始日期 (YYYY-MM-DD)
    - date_to: 结束日期 (YYYY-MM-DD)
    - sort: 排序方式 (relevance/date/popularity)
    - page: 页码
    - page_size: 每页数量
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort_by = request.GET.get('sort', 'relevance')

    if not query or len(query) < 2:
        return Response({
            'shows': [],
            'episodes': [],
            'comments': [],
            'total': 0,
            'query': query
        })

    # 构建基础查询条件
    q_filter = Q(title__icontains=query) | Q(description__icontains=query)

    shows_list = []
    episodes_list = []
    comments_list = []

    # 搜索播客节目
    if search_type in ['all', 'show']:
        shows_query = Show.objects.filter(
            q_filter,
            is_active=True
        ).select_related('creator', 'category').prefetch_related('tags')

        # 应用分类过滤
        if category_id:
            shows_query = shows_query.filter(category_id=category_id)

        # 应用标签过滤
        if tag_id:
            shows_query = shows_query.filter(tags__id=tag_id)

        # 应用日期过滤
        if date_from:
            shows_query = shows_query.filter(created_at__gte=date_from)
        if date_to:
            shows_query = shows_query.filter(created_at__lte=date_to)

        # 排序
        if sort_by == 'date':
            shows_query = shows_query.order_by('-created_at')
        elif sort_by == 'popularity':
            shows_query = shows_query.order_by('-followers_count', '-play_count')

        shows_list = list(shows_query[:50])

        # 相关度排序
        if sort_by == 'relevance':
            shows_list.sort(key=lambda x: _calculate_relevance_score(x, query), reverse=True)

        shows_list = shows_list[:20]

    # 搜索单集
    if search_type in ['all', 'episode']:
        episodes_query = Episode.objects.filter(
            q_filter,
            status='published'
        ).select_related('show__creator', 'show__category')

        # 应用分类过滤（通过 show）
        if category_id:
            episodes_query = episodes_query.filter(show__category_id=category_id)

        # 应用标签过滤（通过 show）
        if tag_id:
            episodes_query = episodes_query.filter(show__tags__id=tag_id)

        # 应用日期过滤
        if date_from:
            episodes_query = episodes_query.filter(published_at__gte=date_from)
        if date_to:
            episodes_query = episodes_query.filter(published_at__lte=date_to)

        # 排序
        if sort_by == 'date':
            episodes_query = episodes_query.order_by('-published_at')
        elif sort_by == 'popularity':
            episodes_query = episodes_query.order_by('-play_count', '-likes_count')

        episodes_list = list(episodes_query[:50])

        # 相关度排序
        if sort_by == 'relevance':
            episodes_list.sort(key=lambda x: _calculate_relevance_score(x, query), reverse=True)

        episodes_list = episodes_list[:30]

    # 搜索评论
    if search_type in ['all', 'comment']:
        comments_query = Comment.objects.filter(
            text__icontains=query,
            episode__status='published'
        ).select_related('user', 'episode', 'episode__show')

        # 应用日期过滤
        if date_from:
            comments_query = comments_query.filter(created_at__gte=date_from)
        if date_to:
            comments_query = comments_query.filter(created_at__lte=date_to)

        # 排序
        if sort_by == 'date':
            comments_query = comments_query.order_by('-created_at')
        elif sort_by == 'popularity':
            comments_query = comments_query.order_by('-likes_count', '-created_at')
        else:
            comments_query = comments_query.order_by('-created_at')

        comments_list = list(comments_query[:20])

    # 记录搜索
    total_results = len(shows_list) + len(episodes_list) + len(comments_list)
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key if not user else None
    _record_search(query, total_results, user, session_key)

    return Response({
        'shows': ShowListSerializer(shows_list, many=True, context={'request': request}).data,
        'episodes': EpisodeListSerializer(episodes_list, many=True, context={'request': request}).data,
        'comments': CommentSerializer(comments_list, many=True).data,
        'total': total_results,
        'query': query,
        'filters': {
            'type': search_type,
            'category': category_id,
            'tag': tag_id,
            'date_from': date_from,
            'date_to': date_to,
            'sort': sort_by
        }
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


@api_view(['GET'])
@permission_classes([AllowAny])
def search_history(request):
    """
    获取搜索历史
    - 登录用户：返回个人搜索历史
    - 未登录用户：返回会话搜索历史
    """
    limit = int(request.GET.get('limit', 10))

    if request.user.is_authenticated:
        histories = SearchHistory.objects.filter(
            user=request.user
        ).values('query', 'created_at').distinct('query')[:limit]
    else:
        session_key = request.session.session_key
        if not session_key:
            return Response({'results': []})
        histories = SearchHistory.objects.filter(
            session_key=session_key
        ).values('query', 'created_at').distinct('query')[:limit]

    return Response({
        'results': [
            {
                'query': h['query'],
                'timestamp': h['created_at']
            }
            for h in histories
        ]
    })


@api_view(['DELETE'])
def clear_search_history(request):
    """清空搜索历史"""
    if request.user.is_authenticated:
        SearchHistory.objects.filter(user=request.user).delete()
    else:
        session_key = request.session.session_key
        if session_key:
            SearchHistory.objects.filter(session_key=session_key).delete()

    return Response({'message': '搜索历史已清空'})


@api_view(['GET'])
@permission_classes([AllowAny])
def popular_searches(request):
    """
    获取热门搜索
    返回最近7天的热门搜索关键词
    """
    limit = int(request.GET.get('limit', 10))
    seven_days_ago = timezone.now() - timedelta(days=7)

    # 获取最近7天的热门搜索
    popular = PopularSearch.objects.filter(
        last_searched_at__gte=seven_days_ago
    ).order_by('-search_count', '-last_searched_at')[:limit]

    return Response({
        'results': [
            {
                'query': p.query,
                'count': p.search_count
            }
            for p in popular
        ]
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    """
    搜索建议（混合历史和热门）
    """
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))

    suggestions = []

    # 如果有输入，优先返回匹配的热门搜索
    if query:
        popular = PopularSearch.objects.filter(
            query__icontains=query
        ).order_by('-search_count')[:limit]

        suggestions = [
            {
                'query': p.query,
                'type': 'popular',
                'count': p.search_count
            }
            for p in popular
        ]
    else:
        # 无输入时，返回个人历史 + 热门
        if request.user.is_authenticated:
            histories = SearchHistory.objects.filter(
                user=request.user
            ).values('query').distinct()[:5]
        else:
            session_key = request.session.session_key
            if session_key:
                histories = SearchHistory.objects.filter(
                    session_key=session_key
                ).values('query').distinct()[:5]
            else:
                histories = []

        for h in histories:
            suggestions.append({
                'query': h['query'],
                'type': 'history'
            })

        # 补充热门搜索
        remaining = limit - len(suggestions)
        if remaining > 0:
            popular = PopularSearch.objects.order_by('-search_count')[:remaining]
            for p in popular:
                suggestions.append({
                    'query': p.query,
                    'type': 'popular',
                    'count': p.search_count
                })

    return Response({'results': suggestions})
