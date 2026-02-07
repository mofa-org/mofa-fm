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
    - delta: 已发送对话的增量更新（按字流式）
    - complete: 生成完成
    - stream_error: 错误
    """
    from .models import Episode

    # JWT authentication (EventSource doesn't support custom headers)
    token_string = request.GET.get('token')
    if not token_string or token_string == 'null':
        def error_stream():
            yield f"event: stream_error\ndata: {json.dumps({'error': '未提供认证token'})}\n\n"
        return StreamingHttpResponse(error_stream(), content_type='text/event-stream')

    try:
        # 验证JWT token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
    except (TokenError, InvalidToken, User.DoesNotExist) as e:
        def error_stream():
            yield f"event: stream_error\ndata: {json.dumps({'error': '无效的token'})}\n\n"
        return StreamingHttpResponse(error_stream(), content_type='text/event-stream')

    def event_stream():
        try:
            episode = Episode.objects.get(id=episode_id)
        except Episode.DoesNotExist:
            yield f"event: stream_error\ndata: {json.dumps({'error': 'Episode不存在'})}\n\n"
            return

        # 提示客户端重连间隔（毫秒）
        yield "retry: 1000\n\n"

        # 记录已发送的对话数量
        sent_count = 0
        last_sent_content = ""
        poll_interval = 0.5
        max_retries = 480  # 最多等待4分钟（0.5秒 * 480）
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
                last_sent_content = current_dialogue[sent_count - 1].get('content', '')
            elif sent_count > 0 and len(current_dialogue) >= sent_count:
                # 同一条发言内容继续增长，发 delta 事件
                latest_entry = current_dialogue[sent_count - 1]
                latest_content = latest_entry.get('content', '')
                if latest_content != last_sent_content:
                    payload = {
                        "index": sent_count - 1,
                        "participant": latest_entry.get('participant'),
                        "content": latest_content,
                        "timestamp": latest_entry.get('timestamp')
                    }
                    yield f"event: delta\ndata: {json.dumps(payload)}\n\n"
                    last_sent_content = latest_content

            # 检查状态
            if episode.status == 'published':
                yield f"event: complete\ndata: {json.dumps({'status': 'published', 'total': sent_count})}\n\n"
                break
            elif episode.status == 'failed':
                error_message = episode.generation_error or '生成失败'
                yield f"event: stream_error\ndata: {json.dumps({'error': error_message})}\n\n"
                break

            # 等待后再检查
            time.sleep(poll_interval)
            retry_count += 1

        # 超时
        if retry_count >= max_retries:
            yield f"event: stream_error\ndata: {json.dumps({'error': '超时'})}\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response
