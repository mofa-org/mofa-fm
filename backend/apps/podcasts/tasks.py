"""
播客Celery任务
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import os
from utils.audio_processor import process_audio, get_audio_duration
import json


@shared_task
def process_episode_audio(episode_id):
    """
    处理上传的音频文件
    1. 转换为 MP3
    2. 标准化音量
    3. 获取时长和文件大小
    """
    from .models import Episode

    try:
        episode = Episode.objects.get(id=episode_id)
        episode.status = 'processing'
        episode.save()

        input_path = episode.audio_file.path

        # 处理音频
        result = process_audio(input_path)

        if result['success']:
            # 如果生成了新文件，替换原文件
            if result.get('output_path') and result['output_path'] != input_path:
                os.remove(input_path)
                os.rename(result['output_path'], input_path)

            # 更新单集信息
            episode.duration = result['duration']
            episode.file_size = result['file_size']
            episode.status = 'published'
            episode.published_at = timezone.now()
            episode.save()

            # 更新节目统计
            show = episode.show
            show.episodes_count = show.episodes.filter(status='published').count()
            show.save()

            return f"Episode {episode_id} processed successfully"
        else:
            episode.status = 'failed'
            episode.save()
            return f"Episode {episode_id} processing failed: {result['error']}"

    except Exception as e:
        # Log error
        print(f"Error processing audio for episode {episode_id}: {e}")
        # Update status to failed
        try:
            episode = Episode.objects.get(id=episode_id)
            episode.status = 'failed'
            episode.save()
        except Episode.DoesNotExist:
            pass
        raise

@shared_task
def generate_podcast_task(episode_id, script_content, voice_config=None):
    """
    Background task to generate podcast audio from script.
    """
    from .models import Episode
    from .services.generator import PodcastGenerator
    from pydub import AudioSegment
    import os
    from django.conf import settings
    
    episode = None # Initialize episode to None for error handling
    try:
        episode = Episode.objects.get(id=episode_id)
        episode.status = 'processing'
        episode.save()
        
        # Initialize generator
        generator = PodcastGenerator()
        
        # Define output path
        # e.g. media/episodes/YYYY/MM/uuid.mp3
        filename = f"generated_{episode.slug}_{episode.id}.mp3"
        relative_path = f"episodes/{episode.created_at.strftime('%Y/%m')}/{filename}"
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # 清理占位文件，避免残留空文件
        placeholder_name = episode.audio_file.name
        if placeholder_name and placeholder_name != relative_path:
            storage = episode.audio_file.storage
            if storage.exists(placeholder_name):
                storage.delete(placeholder_name)
        
        # Generate
        generator.generate(script_content, full_path, voice_config=voice_config)

        # Update episode
        episode.audio_file.name = relative_path
        episode.script = script_content  # 保存脚本，默认使用AI生成的脚本
        episode.status = 'published'
        episode.duration = int(AudioSegment.from_mp3(full_path).duration_seconds)
        episode.file_size = os.path.getsize(full_path)
        episode.published_at = timezone.now()
        episode.save()

        # 更新节目统计
        show = episode.show
        show.episodes_count = show.episodes.filter(status='published').count()
        show.save()

    except Exception as e:
        print(f"Failed to generate podcast for episode {episode_id}: {e}")
        if episode: # Only update status if episode object was successfully retrieved
            episode.status = 'failed'
            episode.save()
        raise


@shared_task
def generate_debate_task(episode_id, topic, mode='debate', rounds=3):
    """
    Background task to generate debate/conference dialogue (text-only, no audio).

    Args:
        episode_id: Episode ID
        topic: 对话主题（辩题或学习主题）
        mode: 'debate' 或 'conference'
        rounds: 对话轮数
    """
    from .models import Episode
    from .services.conversation import ConversationManager
    from .services.participants import get_participants_by_mode

    episode = None
    try:
        episode = Episode.objects.get(id=episode_id)
        episode.status = 'processing'
        episode.save()

        # 获取参与者配置
        participants = get_participants_by_mode(mode)

        # 保存参与者配置到Episode
        episode.participants_config = [
            {
                "id": p.id,
                "role": p.role,
                "system_prompt": p.system_prompt,
                "voice_id": p.voice_id
            }
            for p in participants
        ]
        episode.save()

        # 创建对话管理器
        manager = ConversationManager(
            participants=participants,
            policy="sequential",
            rounds=rounds
        )

        # 生成对话（流式，每生成一条就保存）
        dialogue_entries = []
        for entry in manager.generate_dialogue(topic):
            dialogue_entries.append(entry)

            # 实时保存，让前端可以看到进度
            episode.dialogue = dialogue_entries.copy()
            episode.save(update_fields=['dialogue'])

            # 显式提交事务，让SSE能立即看到更新
            transaction.commit()

        # 最终保存（确保完整）
        episode.dialogue = dialogue_entries

        # 将对话转换为脚本格式（用于兼容现有前端）
        script_lines = []
        for entry in dialogue_entries:
            participant_config = next(
                (p for p in participants if p.id == entry['participant']),
                None
            )
            if participant_config:
                role_name = participant_config.role
                script_lines.append(f"【{role_name}】{entry['content']}\n")

        episode.script = "\n".join(script_lines)

        # 更新状态为已发布（因为是纯文本，无需音频处理）
        episode.status = 'published'
        episode.published_at = timezone.now()
        episode.save()

        # 更新节目统计（如果关联了show）
        if episode.show_id:  # 使用show_id避免触发RelatedObjectDoesNotExist
            show = episode.show
            show.episodes_count = show.episodes.filter(status='published').count()
            show.save()

        return f"Debate/Conference {episode_id} generated successfully with {len(dialogue_entries)} entries"

    except Exception as e:
        print(f"Failed to generate debate for episode {episode_id}: {e}")
        if episode:
            episode.status = 'failed'
            episode.save()
        raise


@shared_task
def generate_debate_audio_task(episode_id, show_id):
    """
    Background task to generate audio for existing debate/conference Episode.

    Args:
        episode_id: Episode ID (must have dialogue and participants_config)
        show_id: Show ID to associate with
    """
    from .models import Episode, Show
    from .services.generator import PodcastGenerator
    from pydub import AudioSegment
    from django.conf import settings

    episode = None
    try:
        episode = Episode.objects.get(id=episode_id)

        # Validate Episode has dialogue
        if not episode.dialogue or not episode.participants_config:
            raise ValueError("Episode must have dialogue and participants_config")

        # Validate and get Show
        try:
            show = Show.objects.get(id=show_id)
        except Show.DoesNotExist:
            raise ValueError(f"Show {show_id} does not exist")

        episode.status = 'processing'
        episode.save()

        # Initialize generator
        generator = PodcastGenerator()

        # Define output path
        filename = f"debate_{episode.slug}_{episode.id}.mp3"
        relative_path = f"episodes/{episode.created_at.strftime('%Y/%m')}/{filename}"
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Generate audio from dialogue
        generator.generate_multi(
            dialogue=episode.dialogue,
            participants_config=episode.participants_config,
            output_path=full_path
        )

        # Update episode with audio and show association
        episode.audio_file.name = relative_path
        episode.show = show
        episode.status = 'published'
        episode.duration = int(AudioSegment.from_mp3(full_path).duration_seconds)
        episode.file_size = os.path.getsize(full_path)
        episode.published_at = timezone.now()
        episode.save()

        # Update show statistics
        show.episodes_count = show.episodes.filter(status='published').count()
        show.save()

        return f"Debate audio {episode_id} generated successfully and published to show {show_id}"

    except Exception as e:
        print(f"Failed to generate debate audio for episode {episode_id}: {e}")
        if episode:
            episode.status = 'failed'
            episode.save()
        raise


async def stream_debate_response(episode_id: int, room_group_name: str):
    """
    Stream debate response via WebSocket.
    This is an async function for use with WebSocket consumers.
    """
    import asyncio
    from channels.layers import get_channel_layer
    from .models import Episode
    from .services.conversation import ConversationManager
    from .services.participants import get_participants_by_mode

    channel_layer = get_channel_layer()

    try:
        episode = await asyncio.to_thread(Episode.objects.get, id=episode_id)
        mode = episode.mode or 'debate'
        topic = episode.generation_meta.get('topic', '')

        participants = get_participants_by_mode(mode)

        # Send status update
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'status_update',
                'status': 'generating',
                'message': 'AI is thinking...'
            }
        )

        # Create conversation manager with policy
        manager = ConversationManager(
            participants=participants,
            policy='unified_ratio',
            rounds=1
        )
        manager.set_dialogue_log(list(episode.dialogue or []))

        # Stream dialogue entries
        for entry in manager.generate_dialogue(topic):
            await channel_layer.group_send(
                room_group_name,
                {
                    'type': 'dialogue_entry',
                    'entry': {
                        'participant': entry.get('participant'),
                        'role': entry.get('role'),
                        'content': entry.get('content'),
                        'timestamp': entry.get('timestamp'),
                        'is_human': False
                    }
                }
            )

        # Send completion status
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'status_update',
                'status': 'completed',
                'message': 'Response completed'
            }
        )

    except Episode.DoesNotExist:
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'status_update',
                'status': 'error',
                'message': 'Episode not found'
            }
        )
    except Exception as e:
        print(f"Error in stream_debate_response: {e}")
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'status_update',
                'status': 'error',
                'message': str(e)[:100]
            }
        )
