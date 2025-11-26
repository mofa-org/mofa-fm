"""
播客视图
"""
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response

from .models import Category, Tag, Show, Episode, ScriptSession, UploadedReference
from .serializers import (
    CategorySerializer, TagSerializer,
    ShowListSerializer, ShowDetailSerializer, ShowCreateSerializer,
    EpisodeListSerializer, EpisodeDetailSerializer, EpisodeCreateSerializer,
    PodcastGenerationSerializer,
    ScriptSessionSerializer, ScriptSessionCreateSerializer, ScriptChatSerializer,
    UploadedReferenceSerializer
)
from .permissions import IsCreatorOrReadOnly, IsShowOwner

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
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]

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
        queryset = Episode.objects.filter(status='published').select_related('show__creator')

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
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]


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


class GenerateEpisodeView(generics.GenericAPIView):
    """生成播客单集"""
    serializer_class = PodcastGenerationSerializer
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]

    def post(self, request, *args, **kwargs):
        from .tasks import generate_podcast_task

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        show = get_object_or_404(Show, id=data['show_id'], creator=request.user)
        placeholder_file = ContentFile(b'', name=f'pending-{uuid4().hex}.mp3')

        episode = Episode.objects.create(
            show=show,
            title=data['title'],
            description="AI Generated Podcast",
            status='processing',
            audio_file=placeholder_file
        )

        generate_podcast_task.delay(episode.id, data['script'])

        return Response(
            {
                "message": "Podcast generation started",
                "episode_id": episode.id
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

        ai_service = ScriptAIService()

        # 获取所有上传文件的文本
        reference_texts = [
            ref.extracted_text
            for ref in session.uploaded_files.all()
            if ref.extracted_text and ref.extracted_text.strip()
        ]

        messages_for_ai = [
            {
                'role': msg['role'],
                'content': msg['content']
            }
            for msg in session.chat_history
            if msg.get('role') in ('user', 'assistant') and msg.get('content')
        ]

        # 调用AI
        result = ai_service.chat(
            messages=messages_for_ai,
            reference_texts=reference_texts,
            current_script=session.current_script,
            enable_tools=True  # 启用工具调用（Tavily搜索等）
        )

        if not result['success']:
            # 回滚最后一条用户消息，避免污染历史
            if session.chat_history:
                session.chat_history.pop()
                session.save(update_fields=['chat_history'])
            return Response(
                {'error': result.get('error', 'AI调用失败')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

@api_view(['GET'])
@permission_classes([AllowAny])
def trending_sources(request):
    """获取所有可用的热搜榜源"""
    import requests
    from django.conf import settings

    trending_api_url = getattr(settings, 'TRENDING_API_URL', 'http://mofa.fm:1145')

    try:
        response = requests.get(f'{trending_api_url}/all', timeout=10)
        response.raise_for_status()
        return Response(response.json())
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
    from django.conf import settings

    trending_api_url = getattr(settings, 'TRENDING_API_URL', 'http://mofa.fm:1145')

    try:
        response = requests.get(f'{trending_api_url}/{source}', timeout=10)
        response.raise_for_status()
        return Response(response.json())
    except requests.RequestException as e:
        return Response(
            {'error': f'获取热搜数据失败: {str(e)}'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
