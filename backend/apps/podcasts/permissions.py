"""
播客权限
"""
from rest_framework import permissions
from django.db.models import Q


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    只有创作者可以创建内容
    所有人可以读取
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_creator


class IsShowOwner(permissions.BasePermission):
    """
    只有节目所有者可以编辑/删除
    """

    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user


class ShowPermission(permissions.BasePermission):
    """节目级别权限（包含可见性检查）"""

    def has_permission(self, request, view):
        # 列表和创建操作
        if view.action == 'create':
            return request.user and request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        # 读取操作：检查可见性
        if view.action in ['retrieve', 'list']:
            return obj.can_view(request.user)

        # 写入操作：只有创作者
        return request.user and request.user == obj.creator


class EpisodePermission(permissions.BasePermission):
    """单集级别权限（包含可见性检查）"""

    def has_permission(self, request, view):
        # 列表和创建操作
        if view.action == 'create':
            return request.user and request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        # 读取操作：检查可见性
        if view.action in ['retrieve', 'list']:
            return obj.can_view(request.user)

        # 写入操作：只有创作者
        return request.user and request.user == obj.show.creator


def filter_visible_shows(queryset, user):
    """
    过滤出用户可见的节目列表

    Args:
        queryset: Show QuerySet
        user: 当前用户（可能是 None）

    Returns:
        过滤后的 QuerySet
    """
    # 未登录用户：只能看公开的
    if not user or not user.is_authenticated:
        return queryset.filter(
            is_active=True,
            visibility='public'
        )

    # 构建查询条件
    q = Q(visibility='public', is_active=True)  # 公开的
    q |= Q(visibility='unlisted')  # 不公开列出的（任何人都能访问）
    q |= Q(creator=user)  # 自己创建的
    q |= Q(visibility='followers', followers__user=user)  # 已关注的
    q |= Q(visibility='shared', shared_with=user)  # 分享给自己的

    return queryset.filter(q).distinct()


def filter_visible_episodes(queryset, user):
    """
    过滤出用户可见的单集列表

    Args:
        queryset: Episode QuerySet
        user: 当前用户（可能是 None）

    Returns:
        过滤后的 QuerySet
    """
    # 首先过滤节目级别的可见性
    visible_shows_filter = Q()

    if not user or not user.is_authenticated:
        # 未登录：只能看公开节目的公开单集
        visible_shows_filter = Q(
            show__is_active=True,
            show__visibility='public'
        )
    else:
        # 已登录：可以看到自己的、公开的、不公开列出的、关注的、分享的
        visible_shows_filter = (
            Q(show__visibility='public', show__is_active=True) |
            Q(show__visibility='unlisted') |
            Q(show__creator=user) |
            Q(show__visibility='followers', show__followers__user=user) |
            Q(show__visibility='shared', show__shared_with=user)
        )

    # 单集级别的可见性
    episode_filter = Q(status='published')  # 基础：必须已发布

    if not user or not user.is_authenticated:
        # 未登录：单集可见性必须是继承或公开
        episode_filter &= Q(visibility__in=['inherit', 'public', 'unlisted'])
    else:
        # 已登录：除了公开的，还能看到自己的、分享的、关注者可见的
        episode_visibility = (
            Q(visibility='inherit') |  # 继承节目设置
            Q(visibility='public') |
            Q(visibility='unlisted') |
            Q(show__creator=user) |  # 创作者能看到所有状态
            Q(visibility='followers', show__followers__user=user) |
            Q(visibility='shared', shared_with=user)
        )
        episode_filter &= episode_visibility

    return queryset.filter(visible_shows_filter & episode_filter).distinct()


def get_share_suggestions(show, current_user, limit=10):
    """
    获取可以分享给的用户建议

    Args:
        show: Show 对象
        current_user: 当前用户（节目创作者）
        limit: 返回数量

    Returns:
        用户列表
    """
    from apps.users.models import User

    # 排除：自己、已分享的用户
    already_shared = show.shared_with.values_list('id', flat=True)

    # 优先级：
    # 1. 关注了此节目的用户
    # 2. 关注了创作者其他节目的用户
    # 3. 最近活跃的用户

    suggestions = User.objects.exclude(
        id__in=list(already_shared) + [current_user.id]
    ).filter(
        is_active=True
    ).order_by('-last_login')[:limit]

    return suggestions
