"""
互动路由
"""
from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    # 评论
    path('episodes/<int:episode_id>/comments/', views.CommentListView.as_view(), name='comment_list'),
    path('comments/create/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),

    # 点赞
    path('episodes/<int:episode_id>/like/', views.toggle_like, name='toggle_like'),

    # 关注
    path('shows/<int:show_id>/follow/', views.toggle_follow, name='toggle_follow'),
    path('following/', views.MyFollowingView.as_view(), name='my_following'),

    # 播放历史
    path('play/update/', views.update_play_progress, name='update_play_progress'),
    path('play/history/', views.MyPlayHistoryView.as_view(), name='my_play_history'),
    path('play/continue/', views.continue_listening, name='continue_listening'),
]
