"""
播客路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import sse_views

app_name = 'podcasts'

# 创建路由器用于ViewSet
router = DefaultRouter()
router.register(r'script-sessions', views.ScriptSessionViewSet, basename='script-session')
router.register(r'rss-sources', views.RSSSourceViewSet, basename='rss-source')
router.register(r'rss-lists', views.RSSListViewSet, basename='rss-list')
router.register(r'rss-schedules', views.RSSScheduleViewSet, basename='rss-schedule')
router.register(r'rss-runs', views.RSSRunViewSet, basename='rss-run')

urlpatterns = [
    # 分类和标签
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('tags/', views.TagListView.as_view(), name='tag_list'),

    # 统计
    path('stats/', views.stats, name='stats'),
    path('recommendations/episodes/', views.recommended_episodes, name='recommended_episodes'),

    # 播客节目
    path('shows/', views.ShowListView.as_view(), name='show_list'),
    path('shows/create/', views.ShowCreateView.as_view(), name='show_create'),
    path('shows/<slug:slug>/', views.ShowDetailView.as_view(), name='show_detail'),
    path('shows/<slug:slug>/update/', views.ShowUpdateView.as_view(), name='show_update'),
    path('shows/<slug:slug>/delete/', views.ShowDeleteView.as_view(), name='show_delete'),
    path('shows/<slug:slug>/cover-options/', views.generate_show_cover_options, name='generate_show_cover_options'),
    path('shows/<slug:slug>/cover-apply/', views.apply_show_cover_option, name='apply_show_cover_option'),
    path('shows/<slug:slug>/share-card/', views.show_share_card, name='show_share_card'),

    # 单集
    path('episodes/', views.EpisodeListView.as_view(), name='episode_list'),
    path('episodes/create/', views.EpisodeCreateView.as_view(), name='episode_create'),
    path('episodes/generate/', views.GenerateEpisodeView.as_view(), name='episode_generate'),
    path('episodes/generate-from-rss/', views.GenerateEpisodeFromRSSView.as_view(), name='episode_generate_from_rss'),
    path('episodes/generate-from-source/', views.GenerateEpisodeFromSourceView.as_view(), name='episode_generate_from_source'),
    path('episodes/create-from-web/', views.create_episode_from_web, name='episode_create_from_web'),
    path('episodes/generate-debate/', views.generate_debate, name='generate_debate'),
    path('episodes/<int:episode_id>/', views.get_episode_by_id, name='get_episode_by_id'),
    path('episodes/<int:episode_id>/debate-message/', views.debate_message, name='debate_message'),
    path('episodes/<int:episode_id>/share-card/', views.episode_share_card, name='episode_share_card'),
    path('episodes/<int:episode_id>/retry/', views.retry_generation, name='retry_generation'),
    path('episodes/<int:episode_id>/cover-options/', views.generate_cover_options, name='generate_cover_options'),
    path('episodes/<int:episode_id>/cover-apply/', views.apply_cover_option, name='apply_cover_option'),
    path('episodes/<int:episode_id>/stream/', sse_views.debate_stream, name='debate_stream'),  # SSE流
    path('episodes/<int:episode_id>/generate-audio/', views.generate_debate_audio, name='generate_debate_audio'),
    path('episodes/<int:pk>/update/', views.EpisodeUpdateView.as_view(), name='episode_update'),
    path('episodes/<int:pk>/update-script/', views.update_episode_script, name='episode_update_script'),
    path('episodes/<int:pk>/delete/', views.EpisodeDeleteView.as_view(), name='episode_delete'),
    path('shows/<slug:show_slug>/episodes/<slug:episode_slug>/',
         views.EpisodeDetailView.as_view(), name='episode_detail'),

    # 创作者
    path('creator/shows/', views.my_shows, name='my_shows'),
    path('creator/shows/<int:show_id>/episodes/', views.show_episodes, name='show_episodes'),
    path('creator/generation-queue/', views.generation_queue, name='generation_queue'),
    path('creator/tts-voices/', views.tts_voices, name='tts_voices'),

    # 辩论历史
    path('debates/', views.my_debates, name='my_debates'),

    # AI脚本创作 (ViewSet路由)
    path('', include(router.urls)),

    # 热搜榜
    path('trending/sources/', views.trending_sources, name='trending_sources'),
    path('trending/<str:source>/', views.trending_data, name='trending_data'),
]
