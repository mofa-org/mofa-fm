"""
播客视图
"""
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Category, Tag, Show, Episode
from .serializers import (
    CategorySerializer, TagSerializer,
    ShowListSerializer, ShowDetailSerializer, ShowCreateSerializer,
    EpisodeListSerializer, EpisodeDetailSerializer, EpisodeCreateSerializer
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


class GenerateEpisodeView(generics.GenericAPIView):
    """生成播客单集"""
    serializer_class = EpisodeCreateSerializer # Just for documentation, actually uses PodcastGenerationSerializer
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]
    
    def post(self, request, *args, **kwargs):
        from .serializers import PodcastGenerationSerializer
        from .tasks import generate_podcast_task
        
        serializer = PodcastGenerationSerializer(data=request.data, context={'context': request})
        if serializer.is_valid():
            data = serializer.validated_data
            show_id = data['show_id']
            title = data['title']
            script = data['script']
            
            # Create Episode placeholder
            show = Show.objects.get(id=show_id)
            episode = Episode.objects.create(
                show=show,
                title=title,
                description="AI Generated Podcast",
                status='processing',
                audio_file='placeholder.mp3' # Will be updated by task
            )
            
            # Trigger task
            generate_podcast_task.delay(episode.id, script)
            
            return Response({
                "message": "Podcast generation started",
                "episode_id": episode.id
            }, status=status.HTTP_202_ACCEPTED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
