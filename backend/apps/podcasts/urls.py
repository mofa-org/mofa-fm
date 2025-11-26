"""
播客路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'podcasts'

# 创建路由器用于ViewSet
router = DefaultRouter()
router.register(r'script-sessions', views.ScriptSessionViewSet, basename='script-session')

urlpatterns = [
    # 分类和标签
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('tags/', views.TagListView.as_view(), name='tag_list'),

    # 统计
    path('stats/', views.stats, name='stats'),

    # 播客节目
    path('shows/', views.ShowListView.as_view(), name='show_list'),
    path('shows/create/', views.ShowCreateView.as_view(), name='show_create'),
    path('shows/<slug:slug>/', views.ShowDetailView.as_view(), name='show_detail'),
    path('shows/<slug:slug>/update/', views.ShowUpdateView.as_view(), name='show_update'),
    path('shows/<slug:slug>/delete/', views.ShowDeleteView.as_view(), name='show_delete'),

    # 单集
    path('episodes/', views.EpisodeListView.as_view(), name='episode_list'),
    path('episodes/create/', views.EpisodeCreateView.as_view(), name='episode_create'),
    path('episodes/generate/', views.GenerateEpisodeView.as_view(), name='episode_generate'),
    path('episodes/<int:pk>/update/', views.EpisodeUpdateView.as_view(), name='episode_update'),
    path('episodes/<int:pk>/delete/', views.EpisodeDeleteView.as_view(), name='episode_delete'),
    path('shows/<slug:show_slug>/episodes/<slug:episode_slug>/',
         views.EpisodeDetailView.as_view(), name='episode_detail'),

    # 创作者
    path('creator/shows/', views.my_shows, name='my_shows'),
    path('creator/shows/<int:show_id>/episodes/', views.show_episodes, name='show_episodes'),
    path('creator/generation-queue/', views.generation_queue, name='generation_queue'),

    # AI脚本创作 (ViewSet路由)
    path('', include(router.urls)),

    # 热搜榜
    path('trending/sources/', views.trending_sources, name='trending_sources'),
    path('trending/<str:source>/', views.trending_data, name='trending_data'),
]
