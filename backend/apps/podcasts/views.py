"""
播客视图
"""
import os
import re
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response

from .models import (
    Category, Tag, Show, Episode, ScriptSession, UploadedReference,
    RSSSource, RSSList, RSSSchedule, RSSRun,
)
from .serializers import (
    CategorySerializer, TagSerializer,
    ShowListSerializer, ShowDetailSerializer, ShowCreateSerializer,
    EpisodeListSerializer, EpisodeDetailSerializer, EpisodeCreateSerializer,
    PodcastGenerationSerializer, RSSPodcastGenerationSerializer, SourcePodcastGenerationSerializer,
    ScriptSessionSerializer, ScriptSessionCreateSerializer, ScriptChatSerializer,
    UploadedReferenceSerializer,
    RSSSourceSerializer, RSSListSerializer, RSSScheduleSerializer, RSSRunSerializer,
)
from .permissions import IsShowOwner
from .services.speaker_config import normalize_speaker_config, apply_speaker_names
from .services.rss_schedule import compute_next_run_at
from slugify import slugify as awesome_slugify

User = get_user_model()


# 分类和标签

class CategoryListView(generics.ListAPIView):
    """分类列表"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class TagListView(generics.ListAPIView):
    """标签列表"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


# 播客节目

class ShowListView(generics.ListAPIView):
    """播客节目列表"""
    serializer_class = ShowListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'creator']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'total_plays', 'followers_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return Show.objects.filter(is_active=True).select_related('creator', 'category')


class ShowDetailView(generics.RetrieveAPIView):
    """播客节目详情"""
    serializer_class = ShowDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Show.objects.filter(is_active=True).select_related(
            'creator', 'category'
        ).prefetch_related('tags')


class ShowCreateView(generics.CreateAPIView):
    """创建播客节目"""
    serializer_class = ShowCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


class ShowUpdateView(generics.UpdateAPIView):
    """更新播客节目"""
    serializer_class = ShowCreateSerializer
    permission_classes = [IsAuthenticated, IsShowOwner]
    lookup_field = 'slug'

    def get_queryset(self):
        return Show.objects.filter(creator=self.request.user)


class ShowDeleteView(generics.DestroyAPIView):
    """删除播客节目"""
    permission_classes = [IsAuthenticated, IsShowOwner]
    lookup_field = 'slug'

    def get_queryset(self):
        return Show.objects.filter(creator=self.request.user)


# 播客单集

class EpisodeListView(generics.ListAPIView):
    """单集列表"""
    serializer_class = EpisodeListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['show', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['published_at', 'play_count', 'created_at']
    ordering = ['-published_at']

    def get_queryset(self):
        queryset = Episode.objects.filter(
            status='published',
            published_at__isnull=False
        ).select_related('show__creator')

        # 如果提供了 show_slug，过滤该节目的单集
        show_slug = self.request.query_params.get('show_slug')
        if show_slug:
            queryset = queryset.filter(show__slug=show_slug)

        return queryset


class EpisodeDetailView(generics.RetrieveAPIView):
    """单集详情"""
    serializer_class = EpisodeDetailSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        show_slug = self.kwargs.get('show_slug')
        episode_slug = self.kwargs.get('episode_slug')
        return get_object_or_404(
            Episode.objects.filter(status='published').select_related('show__creator'),
            show__slug=show_slug,
            slug=episode_slug
        )


class EpisodeCreateView(generics.CreateAPIView):
    """上传单集"""
    serializer_class = EpisodeCreateSerializer
    permission_classes = [IsAuthenticated]


class EpisodeUpdateView(generics.UpdateAPIView):
    """更新单集"""
    serializer_class = EpisodeCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Episode.objects.filter(show__creator=self.request.user)


class EpisodeDeleteView(generics.DestroyAPIView):
    """删除单集"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Episode.objects.filter(show__creator=self.request.user)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_episode_script(request, pk):
    """更新单集脚本 - 允许创作者微调TTS发音"""
    try:
        episode = Episode.objects.get(pk=pk, show__creator=request.user)
    except Episode.DoesNotExist:
        return Response(
            {'error': '单集不存在或您没有权限'},
            status=status.HTTP_404_NOT_FOUND
        )

    script = request.data.get('script', '')
    if script is None:
        return Response(
            {'error': '请提供脚本内容'},
            status=status.HTTP_400_BAD_REQUEST
        )

    episode.script = script
    episode.save(update_fields=['script', 'updated_at'])

    serializer = EpisodeDetailSerializer(episode, context={'request': request})
    return Response(serializer.data)


# 统计

@api_view(['GET'])
def stats(request):
    """平台统计"""
    from django.db.models import Count, Sum

    data = {
        'total_shows': Show.objects.filter(is_active=True).count(),
        'total_episodes': Episode.objects.filter(status='published').count(),
        'total_creators': User.objects.filter(is_creator=True).count(),
        'total_plays': Episode.objects.filter(status='published').aggregate(
            Sum('play_count')
        )['play_count__sum'] or 0,
    }

    return Response(data)


# 创作者专用

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_shows(request):
    """我的播客节目"""
    from .services.default_show import get_or_create_default_show, DEFAULT_SHOW_SLUG_PREFIX

    default_slug = f'{DEFAULT_SHOW_SLUG_PREFIX}-{request.user.id}'
    if Show.objects.filter(creator=request.user, slug=default_slug).exists():
        get_or_create_default_show(request.user)

    shows = Show.objects.filter(creator=request.user).select_related('category')
    serializer = ShowListSerializer(shows, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def show_episodes(request, show_id):
    """节目的所有单集（包括草稿）"""
    show = get_object_or_404(Show, id=show_id, creator=request.user)
    episodes = show.episodes.all().order_by('-created_at')
    serializer = EpisodeListSerializer(episodes, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generation_queue(request):
    """当前用户的AI生成任务队列"""
    allowed_statuses = {code for code, _ in Episode.STATUS_CHOICES}
    default_statuses = {'processing', 'failed', 'published'}

    requested_status = request.query_params.getlist('status')
    if not requested_status:
        single_status = request.query_params.get('status')
        if single_status:
            requested_status = [s.strip() for s in single_status.split(',') if s.strip()]

    if requested_status:
        statuses = [status for status in requested_status if status in allowed_statuses]
    else:
        statuses = list(default_statuses)

    if not statuses:
        statuses = list(default_statuses)

    episodes = (
        Episode.objects
        .filter(show__creator=request.user, status__in=statuses, description__icontains='AI Generated Podcast')
        .select_related('show')
        .order_by('-created_at')
    )
    serializer = EpisodeListSerializer(episodes, many=True, context={'request': request})
    return Response(serializer.data)


class RSSSourceViewSet(viewsets.ModelViewSet):
    """RSS 源管理"""
    serializer_class = RSSSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RSSSource.objects.filter(creator=self.request.user).order_by('-updated_at')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class RSSListViewSet(viewsets.ModelViewSet):
    """RSS 列表管理"""
    serializer_class = RSSListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            RSSList.objects.filter(creator=self.request.user)
            .prefetch_related('sources')
            .order_by('-updated_at')
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class RSSScheduleViewSet(viewsets.ModelViewSet):
    """RSS 自动化规则管理"""
    serializer_class = RSSScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            RSSSchedule.objects.filter(creator=self.request.user)
            .select_related('rss_list', 'show')
            .order_by('-updated_at')
        )

    def perform_create(self, serializer):
        instance = serializer.save(creator=self.request.user)
        instance.next_run_at = compute_next_run_at(instance) if instance.is_active else None
        instance.save(update_fields=['next_run_at', 'updated_at'])

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.next_run_at = compute_next_run_at(instance) if instance.is_active else None
        instance.save(update_fields=['next_run_at', 'updated_at'])

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """手动执行一次"""
        from .tasks import run_rss_schedule_task

        schedule = self.get_object()
        schedule.last_status = 'queued'
        schedule.last_error = ''
        schedule.save(update_fields=['last_status', 'last_error', 'updated_at'])
        run_rss_schedule_task.delay(schedule.id, trigger_type='manual')
        return Response(
            {'message': '手动任务已提交', 'schedule_id': schedule.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['get'])
    def runs(self, request, pk=None):
        """查看该规则最近执行记录"""
        schedule = self.get_object()
        runs = schedule.runs.select_related('episode').order_by('-started_at')[:30]
        serializer = RSSRunSerializer(runs, many=True, context={'request': request})
        return Response({'count': len(runs), 'results': serializer.data})


class RSSRunViewSet(viewsets.ReadOnlyModelViewSet):
    """RSS 执行记录"""
    serializer_class = RSSRunSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            RSSRun.objects.filter(schedule__creator=self.request.user)
            .select_related('schedule', 'episode')
            .order_by('-started_at')
        )
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            queryset = queryset.filter(schedule_id=schedule_id)
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tts_voices(request):
    """获取可用 TTS 音色列表"""
    from .services.voice_catalog import get_available_tts_voices

    language = (request.query_params.get('language') or 'zh').strip().lower()
    refresh = (request.query_params.get('refresh') or '').strip().lower() in {'1', 'true', 'yes', 'y', 'on'}

    try:
        result = get_available_tts_voices(language=language, force_refresh=refresh)
    except Exception as e:
        return Response(
            {'error': f'获取音色列表失败: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def recommended_episodes(request):
    """站内推荐位：返回可直接展示的单集列表"""
    from apps.interactions.models import Follow, PlayHistory

    raw_limit = request.query_params.get('limit', 6)
    try:
        limit = max(1, min(int(raw_limit), 20))
    except (TypeError, ValueError):
        limit = 6

    base_queryset = Episode.objects.filter(
        status='published',
        show__is_active=True,
    ).select_related('show__creator', 'show__category')

    ranked = []
    seen_episode_ids = set()

    def append_queryset(queryset, reason):
        for item in queryset:
            if item.id in seen_episode_ids:
                continue
            seen_episode_ids.add(item.id)
            ranked.append((item, reason))
            if len(ranked) >= limit:
                break

    if request.user.is_authenticated:
        followed_show_ids = list(
            Follow.objects.filter(user=request.user).values_list('show_id', flat=True)
        )
        if followed_show_ids:
            append_queryset(
                base_queryset.filter(show_id__in=followed_show_ids).order_by('-published_at')[: limit * 3],
                '来自你订阅的内容',
            )

        recent_show_ids = list(
            PlayHistory.objects.filter(user=request.user)
            .values_list('episode__show_id', flat=True)
            .distinct()[:20]
        )
        if recent_show_ids:
            append_queryset(
                base_queryset.filter(show_id__in=recent_show_ids).order_by('-play_count', '-published_at')[: limit * 3],
                '近期相关',
            )

    append_queryset(
        base_queryset.order_by('-play_count', '-like_count', '-published_at')[: limit * 4],
        '热门',
    )
    append_queryset(
        base_queryset.order_by('-published_at')[: limit * 4],
        '最新上架',
    )

    payload = []
    for item, reason in ranked[:limit]:
        payload.append({
            'reason': reason,
            'episode': EpisodeListSerializer(item, context={'request': request}).data,
        })

    return Response({
        'count': len(payload),
        'items': payload,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def episode_share_card(request, episode_id):
    """生成分享卡片所需信息（前端据此绘制海报）"""
    episode = get_object_or_404(
        Episode.objects.select_related('show', 'show__creator'),
        id=episode_id,
        status='published',
    )

    if not episode.show:
        return Response(
            {'error': '该单集未绑定节目，暂不可生成分享卡片'},
            status=status.HTTP_400_BAD_REQUEST
        )

    show_path = f"/shows/{episode.show.slug}/episodes/{episode.slug}"
    share_url = request.build_absolute_uri(show_path)
    description = re.sub(r'\s+', ' ', (episode.description or '').strip())
    if len(description) > 120:
        description = description[:117] + '...'

    share_text = (
        f"{episode.title} | {episode.show.title}\n"
        f"{description}\n"
        f"收听链接：{share_url}"
    )

    return Response({
        'title': episode.title,
        'show_title': episode.show.title,
        'creator_name': episode.show.creator.username,
        'description': description,
        'cover_url': episode.cover_url,
        'share_url': share_url,
        'web_path': show_path,
        'share_text': share_text,
        'published_at': episode.published_at,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retry_generation(request, episode_id):
    """重试失败的 AI 生成任务"""
    from .tasks import generate_podcast_task, generate_source_podcast_task, generate_rss_podcast_task

    episode = get_object_or_404(Episode, id=episode_id, show__creator=request.user)
    if episode.status != 'failed':
        return Response(
            {'error': '仅失败任务可重试'},
            status=status.HTTP_400_BAD_REQUEST
        )

    generation_meta = dict(episode.generation_meta or {})
    source_url = generation_meta.get('source_url')
    rss_urls = generation_meta.get('rss_urls') or []
    max_items = generation_meta.get('max_items', 8)
    template = generation_meta.get('template', 'news_flash')
    deduplicate = generation_meta.get('deduplicate', True)
    sort_by = generation_meta.get('sort_by', 'latest')
    generation_type = generation_meta.get('type')
    script_mode = generation_meta.get('script_mode')
    speaker_config = normalize_speaker_config(generation_meta.get('speaker_config'))

    episode.status = 'processing'
    episode.generation_stage = 'queued'
    episode.generation_error = ''
    episode.save(update_fields=['status', 'generation_stage', 'generation_error', 'updated_at'])

    if generation_type == 'rss' and script_mode == 'manual' and episode.script:
        if speaker_config:
            generate_podcast_task.delay(
                episode.id,
                episode.script,
                speaker_config=speaker_config,
            )
        else:
            generate_podcast_task.delay(episode.id, episode.script)
    elif generation_type == 'rss' and rss_urls:
        if speaker_config:
            generate_rss_podcast_task.delay(
                episode.id,
                rss_urls,
                max_items,
                deduplicate,
                sort_by,
                template,
                speaker_config=speaker_config,
            )
        else:
            generate_rss_podcast_task.delay(
                episode.id,
                rss_urls,
                max_items,
                deduplicate,
                sort_by,
                template,
            )
    elif source_url and generation_type in {'source', 'webpage', 'web'}:
        if speaker_config:
            generate_source_podcast_task.delay(
                episode.id,
                source_url,
                max_items,
                template,
                speaker_config=speaker_config,
            )
        else:
            generate_source_podcast_task.delay(
                episode.id,
                source_url,
                max_items,
                template,
            )
    elif episode.script:
        if speaker_config:
            generate_podcast_task.delay(
                episode.id,
                episode.script,
                speaker_config=speaker_config,
            )
        else:
            generate_podcast_task.delay(episode.id, episode.script)
    else:
        episode.status = 'failed'
        episode.generation_stage = 'failed'
        episode.generation_error = '缺少可重试的脚本或来源链接'
        episode.save(update_fields=['status', 'generation_stage', 'generation_error', 'updated_at'])
        return Response(
            {'error': '缺少可重试的上下文'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {'message': '重试任务已提交', 'episode_id': episode.id},
        status=status.HTTP_202_ACCEPTED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_show_cover_options(request, slug):
    """为节目生成多张封面候选图"""
    from .services.cover_ai import generate_show_cover_candidates

    show = get_object_or_404(Show, slug=slug, creator=request.user)
    try:
        count = int(request.data.get('count', 4))
    except (TypeError, ValueError):
        count = 4
    count = max(1, min(count, 8))

    try:
        candidates = generate_show_cover_candidates(show, count=count)
    except Exception as e:
        return Response({'error': f'封面生成失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            'show_id': show.id,
            'count': len(candidates),
            'candidates': candidates,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_show_cover_option(request, slug):
    """应用候选封面图到节目"""
    from .services.cover_ai import apply_show_cover_candidate

    show = get_object_or_404(Show, slug=slug, creator=request.user)
    candidate_path = (request.data.get('candidate_path') or '').strip()
    if not candidate_path:
        return Response({'error': 'candidate_path 不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cover_url = apply_show_cover_candidate(show, candidate_path)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'应用封面失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            'message': '封面已更新',
            'cover_url': cover_url,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cover_options(request, episode_id):
    """为单集生成多张封面候选图"""
    from .services.cover_ai import generate_episode_cover_candidates

    episode = get_object_or_404(Episode, id=episode_id, show__creator=request.user)
    try:
        count = int(request.data.get('count', 4))
    except (TypeError, ValueError):
        count = 4
    count = max(1, min(count, 8))

    try:
        candidates = generate_episode_cover_candidates(episode, count=count)
    except Exception as e:
        return Response({'error': f'封面生成失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            'episode_id': episode.id,
            'count': len(candidates),
            'candidates': candidates,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_cover_option(request, episode_id):
    """应用候选封面图到单集"""
    from .services.cover_ai import apply_episode_cover_candidate

    episode = get_object_or_404(Episode, id=episode_id, show__creator=request.user)
    candidate_path = (request.data.get('candidate_path') or '').strip()
    if not candidate_path:
        return Response({'error': 'candidate_path 不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cover_url = apply_episode_cover_candidate(episode, candidate_path)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'应用封面失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {
            'message': '封面已更新',
            'cover_url': cover_url,
        },
        status=status.HTTP_200_OK
    )


class GenerateEpisodeView(generics.GenericAPIView):
    """生成播客单集"""
    serializer_class = PodcastGenerationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from .tasks import generate_podcast_task
        from .services.default_show import get_or_create_default_show
        import traceback

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            speaker_config = normalize_speaker_config({
                'host_name': data.get('host_name'),
                'guest_name': data.get('guest_name'),
                'host_voice_id': data.get('host_voice_id'),
                'guest_voice_id': data.get('guest_voice_id'),
            })
            if data.get('show_id'):
                show = get_object_or_404(Show, id=data['show_id'], creator=request.user)
            else:
                show, _ = get_or_create_default_show(request.user)
            placeholder_file = ContentFile(b'', name=f'pending-{uuid4().hex}.mp3')
            generation_meta = {'type': 'script'}
            if speaker_config:
                generation_meta['speaker_config'] = speaker_config

            episode = Episode.objects.create(
                show=show,
                title=data['title'],
                description="AI Generated Podcast",
                status='processing',
                generation_stage='queued',
                generation_error='',
                generation_meta=generation_meta,
                audio_file=placeholder_file
            )

            if speaker_config:
                generate_podcast_task.delay(
                    episode.id,
                    data['script'],
                    speaker_config=speaker_config,
                )
            else:
                generate_podcast_task.delay(episode.id, data['script'])

            return Response(
                {
                    "message": "Podcast generation started",
                    "episode_id": episode.id
                },
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            print(f"[GenerateEpisodeView] Error: {e}")
            print(traceback.format_exc())
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateEpisodeFromRSSView(generics.GenericAPIView):
    """从 RSS 源生成播客单集"""
    serializer_class = RSSPodcastGenerationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from .tasks import generate_podcast_task, generate_rss_podcast_task
        from .services.default_show import get_or_create_default_show
        from .services.rss_ingest import generate_script_from_rss_sources

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        rss_urls = data.get('rss_urls', [data['rss_url']])
        deduplicate = data.get('deduplicate', True)
        sort_by = data.get('sort_by', 'latest')
        template = data.get('template', 'news_flash')
        manual_script = (data.get('script') or '').strip()
        speaker_config = normalize_speaker_config({
            'host_name': data.get('host_name'),
            'guest_name': data.get('guest_name'),
            'host_voice_id': data.get('host_voice_id'),
            'guest_voice_id': data.get('guest_voice_id'),
        })

        if data.get('dry_run', False):
            rss_result = generate_script_from_rss_sources(
                rss_urls=rss_urls,
                max_items=data.get('max_items', 8),
                deduplicate=deduplicate,
                sort_by=sort_by,
                template=template,
            )
            script = apply_speaker_names(rss_result['script'], speaker_config)
            feed_title = rss_result['feed_title']
            items = rss_result['items']
            return Response(
                {
                    "message": "RSS parsed and script generated",
                    "feed_title": feed_title,
                    "item_count": len(items),
                    "items": items,
                    "script": script,
                },
                status=status.HTTP_200_OK
            )

        if data.get('show_id'):
            show = get_object_or_404(Show, id=data['show_id'], creator=request.user)
        else:
            show, _ = get_or_create_default_show(request.user)
        raw_title = (data.get('title') or '').strip()
        auto_title = not raw_title
        title = raw_title or f"RSS 任务 {uuid4().hex[:6]}"
        placeholder_file = ContentFile(b'', name=f'pending-{uuid4().hex}.mp3')
        generation_meta = {
            'type': 'rss',
            'source_url': rss_urls[0],
            'rss_urls': rss_urls,
            'max_items': data.get('max_items', 8),
            'template': template,
            'deduplicate': deduplicate,
            'sort_by': sort_by,
            'auto_title': auto_title,
        }
        if speaker_config:
            generation_meta['speaker_config'] = speaker_config
        if manual_script:
            generation_meta['script_mode'] = 'manual'

        episode = Episode.objects.create(
            show=show,
            title=title,
            description=f"AI Generated Podcast from RSS: {', '.join(rss_urls)}",
            status='processing',
            generation_stage='queued',
            generation_error='',
            generation_meta=generation_meta,
            audio_file=placeholder_file
        )

        scheduled_at = data.get('scheduled_at')
        if manual_script:
            normalized_script = apply_speaker_names(manual_script, speaker_config)
            episode.script = normalized_script
            episode.save(update_fields=['script', 'updated_at'])

            if scheduled_at:
                if speaker_config:
                    generate_podcast_task.apply_async(
                        args=(episode.id, normalized_script),
                        kwargs={'speaker_config': speaker_config},
                        eta=scheduled_at,
                    )
                else:
                    generate_podcast_task.apply_async(args=(episode.id, normalized_script), eta=scheduled_at)
            else:
                if speaker_config:
                    generate_podcast_task.delay(
                        episode.id,
                        normalized_script,
                        speaker_config=speaker_config,
                    )
                else:
                    generate_podcast_task.delay(episode.id, normalized_script)

            return Response(
                {
                    "message": "RSS 脚本已提交并开始生成音频" if not scheduled_at else "RSS 脚本定时任务已提交",
                    "episode_id": episode.id,
                },
                status=status.HTTP_202_ACCEPTED
            )

        task_args = (
            episode.id,
            rss_urls,
            data.get('max_items', 8),
            deduplicate,
            sort_by,
            template,
        )
        if scheduled_at:
            if speaker_config:
                generate_rss_podcast_task.apply_async(
                    args=task_args,
                    kwargs={'speaker_config': speaker_config},
                    eta=scheduled_at,
                )
            else:
                generate_rss_podcast_task.apply_async(args=task_args, eta=scheduled_at)
        else:
            if speaker_config:
                generate_rss_podcast_task.delay(*task_args, speaker_config=speaker_config)
            else:
                generate_rss_podcast_task.delay(*task_args)

        return Response(
            {
                "message": "RSS podcast generation scheduled" if scheduled_at else "RSS podcast generation started",
                "episode_id": episode.id,
            },
            status=status.HTTP_202_ACCEPTED
        )


class GenerateEpisodeFromSourceView(generics.GenericAPIView):
    """从链接源（RSS/网页）生成播客单集"""
    serializer_class = SourcePodcastGenerationSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from .tasks import generate_source_podcast_task
        from .services.default_show import get_or_create_default_show
        from .services.source_ingest import generate_script_from_source

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        speaker_config = normalize_speaker_config({
            'host_name': data.get('host_name'),
            'guest_name': data.get('guest_name'),
            'host_voice_id': data.get('host_voice_id'),
            'guest_voice_id': data.get('guest_voice_id'),
        })

        if data.get('dry_run', False):
            source_result = generate_script_from_source(
                source_url=data['source_url'],
                max_items=data.get('max_items', 8),
                template=data.get('template', 'news_flash'),
            )
            script = apply_speaker_names(source_result['script'], speaker_config)
            source_title = source_result['source_title']
            source_type = source_result['source_type']
            items = source_result.get('items', [])
            return Response(
                {
                    "message": "Source parsed and script generated",
                    "source_type": source_type,
                    "source_title": source_title,
                    "item_count": len(items),
                    "items": items,
                    "script": script,
                },
                status=status.HTTP_200_OK
            )

        if data.get('show_id'):
            show = get_object_or_404(Show, id=data['show_id'], creator=request.user)
        else:
            show, _ = get_or_create_default_show(request.user)
        raw_title = (data.get('title') or '').strip()
        auto_title = not raw_title
        title = raw_title or f"链接任务 {uuid4().hex[:6]}"
        placeholder_file = ContentFile(b'', name=f'pending-{uuid4().hex}.mp3')
        generation_meta = {
            'type': 'source',
            'source_url': data['source_url'],
            'max_items': data.get('max_items', 8),
            'template': data.get('template', 'news_flash'),
            'auto_title': auto_title,
        }
        if speaker_config:
            generation_meta['speaker_config'] = speaker_config

        episode = Episode.objects.create(
            show=show,
            title=title,
            description=f"AI Generated Podcast from source: {data['source_url']}",
            status='processing',
            generation_stage='queued',
            generation_error='',
            generation_meta=generation_meta,
            audio_file=placeholder_file
        )

        if speaker_config:
            generate_source_podcast_task.delay(
                episode.id,
                data['source_url'],
                data.get('max_items', 8),
                data.get('template', 'news_flash'),
                speaker_config=speaker_config,
            )
        else:
            generate_source_podcast_task.delay(
                episode.id,
                data['source_url'],
                data.get('max_items', 8),
                data.get('template', 'news_flash'),
            )

        return Response(
            {
                "message": "Source podcast generation started",
                "episode_id": episode.id,
            },
            status=status.HTTP_202_ACCEPTED
        )


# AI脚本创作相关视图

class ScriptSessionViewSet(viewsets.ModelViewSet):
    """AI脚本会话视图集"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ScriptSessionCreateSerializer
        return ScriptSessionSerializer

    def get_queryset(self):
        """只返回当前用户的会话"""
        return ScriptSession.objects.filter(creator=self.request.user).prefetch_related('uploaded_files')

    def create(self, request, *args, **kwargs):
        """创建会话后返回完整的序列化数据"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # 使用完整的序列化器返回数据
        response_serializer = ScriptSessionSerializer(instance, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """与AI对话，生成或修改脚本"""
        session = self.get_object()
        serializer = ScriptChatSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']

        # 添加用户消息到历史
        session.add_message('user', user_message)

        # 调用AI服务
        from .services.script_ai import ScriptAIService
        from .services.tools import AITools
        import re
        from datetime import datetime

        ai_service = ScriptAIService()

        # 获取所有上传文件的文本
        reference_texts = [
            ref.extracted_text
            for ref in session.uploaded_files.all()
            if ref.extracted_text and ref.extracted_text.strip()
        ]

        # 使用 AI 判断是否需要搜索
        current_date = datetime.now().strftime('%Y年%m月%d日')

        # 调用轻量级模型快速判断
        from openai import OpenAI
        from django.conf import settings
        import json

        judge_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            timeout=float(getattr(settings, 'OPENAI_JUDGE_TIMEOUT', 20)),
        )

        judge_prompt = f"""今天是 {current_date}。

判断以下用户问题是否需要搜索实时信息，如需搜索，请提取多个关键搜索词。

需要搜索的情况：
1. 涉及时间相关词：今天、昨天、最近、最新、当前等
2. 涉及实时数据：股价、指数、天气、新闻、比分等
3. 明确要求搜索：搜索、查询、查找等
4. 询问最新事件、热点话题

不需要搜索的情况：
1. 知识性问题（如"什么是AI"、"如何写代码"）
2. 创作请求（如"帮我写个脚本"、"生成播客"）
3. 历史事件（明确的过去时间，不涉及"最新"）

用户问题："{user_message}"

输出 JSON 格式：
{{
  "need_search": true/false,
  "queries": ["查询词1", "查询词2", "..."]
}}

说明：
- 如果不需要搜索，返回 {{"need_search": false, "queries": []}}
- 如果需要搜索，返回 1-8 个优化的搜索查询词（根据问题复杂度决定）
- 每个查询词应该：
  1. 包含准确的日期（如涉及"今天"用 {current_date}，"昨天"自动计算）
  2. 关键信息提取（如"沪指"改为"上证指数"）
  3. 不超过20字
  4. 从不同角度覆盖用户问题

查询数量建议：
- 简单问题（1个指标）：1-2个查询
- 中等复杂度（2-3个指标）：2-4个查询
- 复杂问题（多维度/对比）：4-8个查询

示例：
用户："今天沪指和深证怎么样"
输出：{{"need_search": true, "queries": ["{current_date} 上证指数收盘价", "{current_date} 深证成指收盘价"]}}

用户："最近有什么科技新闻"
输出：{{"need_search": true, "queries": ["{current_date} 科技新闻", "最新科技行业动态", "科技公司重大事件"]}}

用户："今天股市行情怎么样，有哪些板块表现好"
输出：{{"need_search": true, "queries": ["{current_date} 上证指数", "{current_date} 深证成指", "{current_date} 创业板指", "{current_date} 涨幅最大板块", "{current_date} 领涨行业"]}}

只输出 JSON，不要其他文字。"""

        try:
            judge_response = judge_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{'role': 'user', 'content': judge_prompt}],
                temperature=0,
                max_tokens=200
            )

            response_text = judge_response.choices[0].message.content.strip()

            # 尝试解析 JSON
            try:
                # 去除可能的 markdown 代码块标记
                if response_text.startswith('```'):
                    response_text = response_text.split('```')[1]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                response_text = response_text.strip()

                result = json.loads(response_text)
                needs_search = result.get('need_search', False)
                search_queries = result.get('queries', [])
            except json.JSONDecodeError:
                # JSON 解析失败，回退
                needs_search = response_text != "NO"
                search_queries = [f"{current_date} {user_message}"] if needs_search else []

        except Exception as e:
            # AI判断失败，回退到关键词检测
            search_keywords = [
                r'今天|昨天|前天|最近|最新|当前|现在',
                r'沪指|上证|深证|股市|股价',
                r'新闻|热点|热门|动态',
                r'搜索|查询|查找|查一下|搜一下',
            ]
            needs_search = any(re.search(pattern, user_message, re.IGNORECASE) for pattern in search_keywords)
            search_queries = [f"{current_date} {user_message}"] if needs_search else []

        # 如果需要搜索，执行多轮查询
        if needs_search and search_queries:
            all_search_results = []

            # 限制最多8个查询
            total_queries = min(len(search_queries), 8)
            for idx, query in enumerate(search_queries[:8], 1):
                try:
                    search_result = AITools.execute_tool('tavily_search', {
                        'query': query,
                        'max_results': 6  # 每个查询返回6条结果，8个查询最多48条
                    })
                    all_search_results.append(f"## 查询 {idx}/{total_queries}: {query}\n{search_result}")
                except Exception as e:
                    all_search_results.append(f"## 查询 {idx}/{total_queries}: {query}\n搜索失败: {str(e)}")

            # 合并所有搜索结果
            combined_results = "\n\n".join(all_search_results)
            pre_search_result = f"【搜索结果 - {current_date}】\n已完成 {total_queries} 个查询\n\n{combined_results}"

            if reference_texts is None:
                reference_texts = []
            reference_texts.insert(0, pre_search_result)

        messages_for_ai = [
            {
                'role': msg['role'],
                'content': msg['content']
            }
            for msg in session.chat_history
            if msg.get('role') in ('user', 'assistant') and msg.get('content')
        ]

        # 调用AI（禁用 function calling，因为我们已经强制搜索了）
        result = ai_service.chat(
            messages=messages_for_ai,
            reference_texts=reference_texts,
            current_script=session.current_script,
            enable_tools=False  # 禁用工具，避免重复搜索
        )

        if not result['success']:
            error_text = str(result.get('error') or 'AI调用失败')
            fallback_message = 'AI 服务暂忙，请稍后再试。'
            lower_error = error_text.lower()
            if 'timeout' in lower_error or 'timed out' in lower_error or '超时' in error_text:
                fallback_message = 'AI 请求超时，请稍后重试。'

            # 保留用户消息，并追加一条系统回退回复，避免前端出现 AxiosError
            session.add_message('assistant', fallback_message)
            return Response(
                {
                    'message': fallback_message,
                    'script': session.current_script,
                    'has_script_update': False,
                    'error': error_text,
                },
                status=status.HTTP_200_OK
            )

        # 添加AI回复到历史
        session.add_message('assistant', result['response'])

        # 如果有新脚本，更新
        new_script = result.get('script')
        script_updated = False

        if new_script:
            new_script = new_script.strip()

        if new_script and new_script != session.current_script:
            session.update_script(new_script)
            script_updated = True

        return Response({
            'message': result['response'],
            'script': session.current_script,
            'has_script_update': script_updated
        })

    @action(detail=True, methods=['post'])
    def preview_segment(self, request, pk=None):
        """段落级试听（局部重生音频）"""
        from django.conf import settings
        from .services.generator import PodcastGenerator

        session = self.get_object()
        segment_text = (request.data.get('segment_text') or '').strip()
        voice_id = (request.data.get('voice_id') or '').strip()

        if not segment_text:
            return Response({'error': 'segment_text 不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r"^【[^】]+】", segment_text):
            return Response({'error': '片段需以【角色】开头'}, status=status.HTTP_400_BAD_REQUEST)

        relative_path = f"previews/{timezone.now().strftime('%Y/%m')}/seg-{session.id}-{uuid4().hex}.mp3"
        output_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        try:
            generator = PodcastGenerator()

            # 如果指定了 voice_id，构建 voice_overrides
            voice_overrides = None
            if voice_id:
                # 从片段中提取角色名
                role_match = re.match(r"^【([^】]+)】", segment_text)
                if role_match:
                    role_name = role_match.group(1).strip()
                    # 获取角色的 alias
                    role_alias = generator.character_aliases.get(role_name)
                    if role_alias:
                        voice_overrides = {role_alias: {"voice_id": voice_id}}

            generator.generate(
                segment_text,
                output_path,
                voice_overrides=voice_overrides
            )
        except Exception as e:
            return Response({'error': f'试听生成失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else settings.MEDIA_URL + '/'
        return Response(
            {
                'message': '试听音频已生成',
                'preview_url': f"{media_url}{relative_path}",
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def rewrite_segment(self, request, pk=None):
        """段落级局部重写"""
        from django.conf import settings
        from openai import OpenAI

        self.get_object()
        segment_text = (request.data.get('segment_text') or '').strip()
        instruction = (request.data.get('instruction') or '').strip()
        if not segment_text:
            return Response({'error': 'segment_text 不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if not instruction:
            return Response({'error': 'instruction 不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        role_match = re.match(r"^(【[^】]+】)", segment_text)
        role_tag = role_match.group(1) if role_match else ""

        try:
            client = OpenAI(
                api_key=getattr(settings, "OPENAI_API_KEY", ""),
                base_url=getattr(settings, "OPENAI_API_BASE", "https://api.openai.com/v1"),
            )
            completion = client.chat.completions.create(
                model=getattr(settings, "OPENAI_MODEL", "openai/gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是播客脚本润色器。只重写给定单段文本，不要输出多段。"
                            "必须保留【角色】标签开头，输出纯文本，不要代码块。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"原片段：\n{segment_text}\n\n"
                            f"改写要求：{instruction}\n\n"
                            "请输出改写后的单段。"
                        ),
                    },
                ],
                temperature=0.6,
            )
            rewritten = (completion.choices[0].message.content or "").strip()
            if not rewritten:
                return Response({'error': '模型返回空结果'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if role_tag and not rewritten.startswith(role_tag):
                rewritten = f"{role_tag}{rewritten}"
            return Response({'rewritten_segment': rewritten}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'局部重写失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def upload_file(self, request, pk=None):
        """上传参考文件"""
        session = self.get_object()

        if 'file' not in request.FILES:
            return Response(
                {'error': '请上传文件'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']

        # 检查文件类型
        import os
        file_ext = os.path.splitext(uploaded_file.name)[1].lower().lstrip('.')

        if file_ext not in ['txt', 'pdf', 'md', 'docx']:
            return Response(
                {'error': f'不支持的文件类型: {file_ext}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 保存文件
        reference = UploadedReference.objects.create(
            session=session,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_type=file_ext,
            file_size=uploaded_file.size
        )

        # 解析文件内容
        from .services.file_parser import FileParser

        parser = FileParser()
        parse_result = parser.parse(reference.file.path, file_ext)

        if parse_result['success']:
            reference.extracted_text = parse_result['text']
            reference.save()
        else:
            # 删除失败的文件
            reference.delete()
            return Response(
                {'error': f'文件解析失败: {parse_result.get("error")}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UploadedReferenceSerializer(reference, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def generate_audio(self, request, pk=None):
        """从脚本生成音频（占位，暂不实现）"""
        session = self.get_object()

        if not session.current_script:
            return Response(
                {'error': '当前没有脚本，请先生成脚本'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: 实现音频生成
        # 这里暂时返回占位响应
        return Response({
            'message': '音频生成功能即将上线',
            'script': session.current_script,
            'status': 'pending'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


# 热搜榜相关视图


def _trending_base_url():
    from django.conf import settings

    raw = (getattr(settings, 'TRENDING_API_URL', '') or '').strip().rstrip('/')
    if not raw:
        raw = 'https://hot.mofa.fm'
    if raw.endswith('/all'):
        raw = raw[:-4].rstrip('/')
    return raw


def _trending_request_json(path: str):
    import time
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    path = path if path.startswith('/') else f'/{path}'
    url = f'{_trending_base_url()}{path}'

    session = requests.Session()
    session.trust_env = False
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.3,
        allowed_methods=frozenset(['GET']),
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    errors = []
    for i in range(3):
        try:
            response = session.get(url, timeout=(5, 15))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.SSLError as exc:
            errors.append(str(exc))
            time.sleep(0.25 * (i + 1))
            continue
        except requests.RequestException:
            raise

    raise requests.exceptions.SSLError('; '.join(errors) or 'TLS handshake failed')

@api_view(['GET'])
@permission_classes([AllowAny])
def trending_sources(request):
    """获取所有可用的热搜榜源"""
    import requests

    try:
        return Response(_trending_request_json('/all'))
    except requests.RequestException as e:
        return Response(
            {'error': f'获取热搜榜源失败: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_data(request, source):
    """获取指定热搜榜的数据"""
    import requests

    try:
        return Response(_trending_request_json(f'/{source}'))
    except requests.RequestException as e:
        return Response(
            {'error': f'获取热搜数据失败: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# Debate/Conference 生成
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_debate(request):
    """
    生成Debate或Conference对话（纯文本，不关联Show）

    Request body:
    {
        "title": "AI是否会取代程序员",
        "topic": "AI是否会取代程序员？",
        "mode": "debate",  # "debate" 或 "conference"
        "rounds": 3
    }
    """
    from .tasks import generate_debate_task
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"generate_debate called by user: {request.user}")
    logger.info(f"Request data: {request.data}")

    title = request.data.get('title')
    topic = request.data.get('topic')
    mode = request.data.get('mode', 'debate')
    rounds = request.data.get('rounds', 1)

    logger.info(f"Extracted - title: {title}, topic: {topic}, mode: {mode}, rounds: {rounds}")

    # 验证
    if not all([title, topic]):
        return Response(
            {'error': 'title, topic 必填'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if mode not in ['debate', 'conference']:
        return Response(
            {'error': 'mode 必须是 debate 或 conference'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        rounds = int(rounds)
    except (TypeError, ValueError):
        return Response(
            {'error': 'rounds 必须是整数'},
            status=status.HTTP_400_BAD_REQUEST
        )
    rounds = max(1, min(rounds, 5))

    # 创建Episode（不关联show）
    episode = Episode.objects.create(
        title=title,
        description=f"AI Generated {mode.capitalize()}",
        status='processing',
        mode=mode,
        generation_meta={
            "creator_id": request.user.id,
            "topic": topic
        }
    )

    # 触发异步任务
    generate_debate_task.delay(episode.id, topic, mode, rounds)

    return Response(
        {
            "message": f"{mode.capitalize()} generation started",
            "episode_id": episode.id,
            "mode": mode
        },
        status=status.HTTP_202_ACCEPTED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debate_message(request, episode_id):
    """
    用户插话：追加一条用户消息，并继续生成一轮AI群聊回复。
    """
    from .tasks import generate_debate_followup_task

    message = (request.data.get('message') or '').strip()
    if not message:
        return Response(
            {'error': 'message 不能为空'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        episode = Episode.objects.get(id=episode_id)
    except Episode.DoesNotExist:
        return Response(
            {'error': 'Episode不存在'},
            status=status.HTTP_404_NOT_FOUND
        )

    if episode.mode not in ['debate', 'conference']:
        return Response(
            {'error': '该Episode不是辩论/会议模式'},
            status=status.HTTP_400_BAD_REQUEST
        )

    creator_id = (episode.generation_meta or {}).get('creator_id')
    if creator_id and int(creator_id) != request.user.id:
        return Response(
            {'error': '您没有权限向该辩论发送消息'},
            status=status.HTTP_403_FORBIDDEN
        )

    topic = (episode.generation_meta or {}).get('topic') or episode.title
    client_id = request.data.get('client_id')  # 客户端消息ID，用于去重

    dialogue = list(episode.dialogue or [])
    entry = {
        'participant': 'user',
        'content': message,
        'timestamp': timezone.now().isoformat()
    }
    if client_id:
        entry['clientId'] = client_id
    dialogue.append(entry)

    episode.dialogue = dialogue
    episode.status = 'processing'
    episode.generation_error = ''
    episode.save(update_fields=['dialogue', 'status', 'generation_error', 'updated_at'])

    generate_debate_followup_task.delay(episode.id, topic, episode.mode)

    return Response(
        {
            "message": "Debate followup started",
            "episode_id": episode.id
        },
        status=status.HTTP_202_ACCEPTED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_debate_audio(request, episode_id):
    """
    为已生成的Debate/Conference Episode生成音频并关联Show

    Request body:
    {
        "show_id": 123  # 可选；不传则自动使用默认节目
    }
    """
    from .tasks import generate_debate_audio_task
    from .services.default_show import get_or_create_default_show

    # 获取并验证Episode
    try:
        episode = Episode.objects.get(id=episode_id)
    except Episode.DoesNotExist:
        return Response(
            {'error': 'Episode不存在'},
            status=status.HTTP_404_NOT_FOUND
        )

    # 验证Episode有对话内容
    if not episode.dialogue or not episode.participants_config:
        return Response(
            {'error': 'Episode缺少对话内容，无法生成音频'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 验证Episode还没有音频
    if episode.audio_file:
        return Response(
            {'error': 'Episode已经有音频文件'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # show_id 可选；未传则自动落到默认节目
    show_id = request.data.get('show_id')
    if show_id:
        try:
            show = Show.objects.get(id=show_id, creator=request.user)
        except Show.DoesNotExist:
            return Response(
                {'error': 'Show不存在或您没有权限'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        show, _ = get_or_create_default_show(request.user)
        show_id = show.id

    # 更新状态
    episode.status = 'processing'
    episode.save()

    # 触发异步任务
    generate_debate_audio_task.delay(episode_id, show_id)

    return Response(
        {
            "message": "Audio generation started",
            "episode_id": episode_id,
            "show_id": show_id
        },
        status=status.HTTP_202_ACCEPTED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_episode_by_id(request, episode_id):
    """
    根据ID获取Episode详情（用于Debate/Conference查看）
    """
    try:
        episode = Episode.objects.select_related('show__creator').get(id=episode_id)
    except Episode.DoesNotExist:
        return Response(
            {'error': 'Episode不存在'},
            status=status.HTTP_404_NOT_FOUND
        )

    if episode.mode in ['debate', 'conference'] and not episode.show_id:
        creator_id = (episode.generation_meta or {}).get('creator_id')
        if creator_id and int(creator_id) != request.user.id:
            return Response(
                {'error': '您没有权限查看该辩论'},
                status=status.HTTP_403_FORBIDDEN
            )

    serializer = EpisodeDetailSerializer(episode, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_debates(request):
    """
    获取当前用户的辩论/会议历史记录（没有关联Show的Episode）
    """
    episodes = Episode.objects.filter(
        show__isnull=True,  # 没有关联Show的Episode
        mode__in=['debate', 'conference'],  # 只获取辩论和会议模式
        generation_meta__creator_id=request.user.id
    ).order_by('-created_at')

    serializer = EpisodeDetailSerializer(episodes, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_episode_from_web(request):
    """
    从网页 URL 创建播客对话会话
    接收网页链接，抓取内容生成播客脚本，创建对话会话供用户编辑
    """
    from .services.web_ingest import fetch_webpage_content, generate_podcast_script_from_web

    url = request.data.get('url')
    show_id = request.data.get('show_id')

    if not url:
        return Response({'error': '请提供网页链接'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 抓取网页内容
        web_content = fetch_webpage_content(url)

        if not web_content.content or len(web_content.content) < 100:
            return Response({'error': '无法提取网页内容，请检查链接是否有效'}, status=status.HTTP_400_BAD_REQUEST)

        # 使用 AI 将网页内容转换为播客脚本
        podcast_script = generate_podcast_script_from_web(web_content)

        if not podcast_script or len(podcast_script) < 100:
            return Response({'error': '无法生成播客脚本，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 创建对话会话，把生成的脚本放进去
        title = web_content.title or f"网页播客 {uuid4().hex[:6]}"
        session = ScriptSession.objects.create(
            creator=request.user,
            title=title,
            current_script=podcast_script,
            chat_history=[
                {
                    'role': 'system',
                    'content': f'已从网页生成播客脚本：{url}',
                    'timestamp': timezone.now().isoformat(),
                },
                {
                    'role': 'assistant',
                    'content': f'我已根据网页内容生成了播客脚本，你可以直接编辑脚本或与我对话修改。',
                    'timestamp': timezone.now().isoformat(),
                }
            ],
            voice_config={
                'target_show_id': show_id,
                'source_url': url,
            } if show_id else {'source_url': url},
        )

        return Response({
            'message': '已从网页生成播客脚本',
            'session_id': session.id,
            'title': title,
            'script': podcast_script,
            'word_count': web_content.word_count,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'处理失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
