"""
搜索路由
"""
from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search, name='search'),
    path('quick/', views.quick_search, name='quick_search'),
]
