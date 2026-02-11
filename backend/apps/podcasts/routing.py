"""
WebSocket routing for podcasts app.
Only used for real-time debate/conference streaming.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/debate/(?P<episode_id>\d+)/$', consumers.DebateConsumer.as_asgi()),
]
