"""
SSE (Server-Sent Events) 视图 - 用于实时流式传输
"""
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
import json
import time

User = get_user_model()


@require_http_methods(["GET"])
def debate_stream(request, episode_id):
    """
    SSE流式传输 - 实时推送debate生成进度

    事件类型：
    - dialogue: 新对话生成
    - status: 状态更新
    - complete: 生成完成
    - error: 错误
    """
    from .models import Episode

    # JWT authentication (EventSource doesn't support custom headers)
    token_string = request.GET.get('token')
    if not token_string or token_string == 'null':
        def error_stream():
            yield f"event: error\ndata: {json.dumps({'error': '未提供认证token'})}\n\n"
        return StreamingHttpResponse(error_stream(), content_type='text/event-stream')

    try:
        # 验证JWT token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
    except (TokenError, InvalidToken, User.DoesNotExist) as e:
        def error_stream():
            yield f"event: error\ndata: {json.dumps({'error': '无效的token'})}\n\n"
        return StreamingHttpResponse(error_stream(), content_type='text/event-stream')

    def event_stream():
        try:
            episode = Episode.objects.get(id=episode_id)
        except Episode.DoesNotExist:
            yield f"event: error\ndata: {json.dumps({'error': 'Episode不存在'})}\n\n"
            return
        
        # 记录已发送的对话数量
        sent_count = 0
        max_retries = 120  # 最多等待4分钟（2秒 * 120）
        retry_count = 0
        
        while retry_count < max_retries:
            episode.refresh_from_db()
            
            # 检查是否有新对话
            current_dialogue = episode.dialogue or []
            if len(current_dialogue) > sent_count:
                # 发送新对话
                for entry in current_dialogue[sent_count:]:
                    yield f"event: dialogue\ndata: {json.dumps(entry)}\n\n"
                sent_count = len(current_dialogue)
            
            # 检查状态
            if episode.status == 'published':
                yield f"event: complete\ndata: {json.dumps({'status': 'published', 'total': sent_count})}\n\n"
                break
            elif episode.status == 'failed':
                yield f"event: error\ndata: {json.dumps({'error': '生成失败'})}\n\n"
                break
            
            # 等待2秒再检查
            time.sleep(2)
            retry_count += 1
        
        # 超时
        if retry_count >= max_retries:
            yield f"event: error\ndata: {json.dumps({'error': '超时'})}\n\n"
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response
