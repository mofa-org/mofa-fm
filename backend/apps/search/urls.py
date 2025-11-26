"""
搜索路由
"""
from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search, name='search'),
    path('quick/', views.quick_search, name='quick_search'),
    path('history/', views.search_history, name='search_history'),
    path('history/clear/', views.clear_search_history, name='clear_search_history'),
    path('popular/', views.popular_searches, name='popular_searches'),
    path('suggestions/', views.search_suggestions, name='search_suggestions'),
]
