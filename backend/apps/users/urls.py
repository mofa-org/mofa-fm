"""
用户路由
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # 认证
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 用户信息
    path('me/', views.current_user, name='current_user'),
    path('me/update/', views.update_profile, name='update_profile'),
    path('users/<str:username>/', views.UserDetailView.as_view(), name='user_detail'),

    # 创作者验证
    path('creator/become/', views.become_creator, name='become_creator'),
    path('creator/verify/', views.verify_creator, name='verify_creator'),
]
