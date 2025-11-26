"""
健康检查视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
import time


class HealthCheckView(APIView):
    """系统健康检查接口"""
    permission_classes = []

    def get(self, request):
        """检查系统各项服务状态"""
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'services': {}
        }

        # 检查数据库
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['services']['database'] = {
                'status': 'operational',
                'message': 'Database connection OK'
            }
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['services']['database'] = {
                'status': 'down',
                'message': str(e)
            }

        # 检查 Redis
        try:
            cache.set('health_check', 'ok', 10)
            cache_value = cache.get('health_check')
            if cache_value == 'ok':
                health_status['services']['redis'] = {
                    'status': 'operational',
                    'message': 'Redis connection OK'
                }
            else:
                raise Exception('Cache value mismatch')
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['services']['redis'] = {
                'status': 'down',
                'message': str(e)
            }

        # 检查 AI 服务配置
        from django.conf import settings
        if settings.OPENAI_API_KEY:
            health_status['services']['ai_script'] = {
                'status': 'operational',
                'message': 'AI script service configured'
            }
        else:
            health_status['services']['ai_script'] = {
                'status': 'down',
                'message': 'API key not configured'
            }

        # 检查 TTS 服务配置
        if settings.MINIMAX_TTS.get('api_key'):
            health_status['services']['tts'] = {
                'status': 'operational',
                'message': 'TTS service configured'
            }
        else:
            health_status['services']['tts'] = {
                'status': 'down',
                'message': 'API key not configured'
            }

        # 返回适当的 HTTP 状态码
        http_status = status.HTTP_200_OK
        if health_status['status'] == 'unhealthy':
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health_status['status'] == 'degraded':
            http_status = status.HTTP_200_OK

        return Response(health_status, status=http_status)
