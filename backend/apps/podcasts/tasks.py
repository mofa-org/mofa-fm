"""
播客Celery任务
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import os
from utils.audio_processor import process_audio, get_audio_duration
import json
import time


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
    Background task to generate podcast audio from script and AI cover.
    """
    from .models import Episode
    from .services.generator import PodcastGenerator
    from .services.cover_ai import generate_episode_cover
    from .services.speaker_config import build_generator_runtime_options
    from pydub import AudioSegment
    import os
    from django.conf import settings

    episode = None # Initialize episode to None for error handling
    try:
        episode = Episode.objects.get(id=episode_id)
        episode.status = 'processing'
        episode.generation_stage = 'generating_audio'
        episode.save()

        # 转换 speaker_config 为 voice_overrides 格式
        character_aliases, voice_overrides = build_generator_runtime_options(voice_config)

        print(f"[DEBUG] Script preview: {script_content[:200]}...")
        print(f"[DEBUG] character_aliases: {character_aliases}")
        print(f"[DEBUG] voice_overrides: {voice_overrides}")

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

        # Generate audio with proper voice overrides
        generator.generate(
            script_content,
            full_path,
            character_aliases=character_aliases,
            voice_overrides=voice_overrides
        )

        # Update episode with audio
        episode.audio_file.name = relative_path
        episode.script = script_content  # 保存脚本，默认使用AI生成的脚本
        episode.duration = int(AudioSegment.from_mp3(full_path).duration_seconds)
        episode.file_size = os.path.getsize(full_path)
        episode.generation_stage = 'generating_cover'
        episode.save()

        # Generate AI cover if not already has one
        if not episode.cover:
            try:
                generate_episode_cover(episode)
            except Exception as cover_err:
                # Cover generation failure should not block audio publishing
                print(f"Cover generation failed for episode {episode_id}: {cover_err}")

        # Mark as published
        episode.status = 'published'
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
            episode.generation_error = str(e)[:1000]
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

        # 保存脚本并标记为草稿状态，等待用户继续编辑或生成音频
        episode.status = 'draft'
        episode.generation_stage = 'script_completed'
        episode.save()

        return f"Debate/Conference {episode_id} script generated successfully with {len(dialogue_entries)} entries"

    except Exception as e:
        print(f"Failed to generate debate for episode {episode_id}: {e}")
        if episode:
            episode.status = 'failed'
            episode.save()
        raise


@shared_task
def generate_debate_audio_task(episode_id, show_id=None, voice_config=None):
    """
    Background task to generate audio for existing debate/conference Episode.

    Args:
        episode_id: Episode ID (must have dialogue and participants_config)
        show_id: Show ID to associate with (optional)
        voice_config: Dict with voice configuration (optional)
            {
                "host_voice_id": "xxx",  # 主持人/正方音色
                "guest_voice_id": "xxx"  # 嘉宾/反方音色
            }
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

        # Get Show if show_id provided
        show = None
        if show_id:
            try:
                show = Show.objects.get(id=show_id)
            except Show.DoesNotExist:
                print(f"Warning: Show {show_id} does not exist, continuing without show association")

        episode.status = 'processing'
        episode.generation_stage = 'audio_generating'
        episode.save()

        # Initialize generator
        generator = PodcastGenerator()

        # Define output path
        filename = f"debate_{episode.slug}_{episode.id}.mp3"
        relative_path = f"episodes/{episode.created_at.strftime('%Y/%m')}/{filename}"
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        # Prepare participants config with voice overrides
        participants_config = episode.participants_config
        if voice_config:
            judge_voice_id = voice_config.get('judge_voice_id')
            host_voice_id = voice_config.get('host_voice_id')
            guest_voice_id = voice_config.get('guest_voice_id')

            # Update participants config with voice IDs
            for participant in participants_config:
                role = participant.get('role', '')
                participant_id = participant.get('id', '')

                # 主持人/裁判使用 judge_voice_id
                if role in ['主持人', '裁判'] or participant_id in ['judge', 'tutor']:
                    if judge_voice_id:
                        participant['voice_id'] = judge_voice_id
                # 正方/嘉宾使用 host_voice_id
                elif role in ['正方辩手', '嘉宾'] or participant_id in ['llm1', 'student1']:
                    if host_voice_id:
                        participant['voice_id'] = host_voice_id
                # 反方/学生使用 guest_voice_id
                elif role in ['反方辩手', '学生'] or participant_id in ['llm2', 'student2']:
                    if guest_voice_id:
                        participant['voice_id'] = guest_voice_id

        # Generate audio from dialogue
        generator.generate_multi(
            dialogue=episode.dialogue,
            participants_config=participants_config,
            output_path=full_path
        )

        # Update episode with audio
        episode.audio_file.name = relative_path
        if show:
            episode.show = show
        episode.status = 'published'
        episode.generation_stage = 'completed'
        episode.duration = int(AudioSegment.from_mp3(full_path).duration_seconds)
        episode.file_size = os.path.getsize(full_path)
        episode.published_at = timezone.now()
        episode.save()

        # Update show statistics if show exists
        if show:
            show.episodes_count = show.episodes.filter(status='published').count()
            show.save()

        return f"Debate audio {episode_id} generated successfully" + (f" and published to show {show_id}" if show else "")

    except Exception as e:
        print(f"Failed to generate debate audio for episode {episode_id}: {e}")
        if episode:
            episode.status = 'failed'
            episode.save()
        raise


@shared_task
def generate_debate_followup_task(episode_id, topic, mode='debate'):
    """
    在现有辩论上继续生成一轮（用于用户插话后的群聊推进）。
    只生成一条AI回复来回应用户消息。
    """
    from .models import Episode
    from .services.conversation import ConversationManager, _build_script_from_dialogue
    from .services.participants import get_participants_by_mode
    from openai import OpenAI
    from django.conf import settings

    episode = None
    try:
        episode = Episode.objects.get(id=episode_id)
        episode.status = 'processing'
        episode.generation_error = ''
        episode.save(update_fields=['status', 'generation_error', 'updated_at'])

        participants = get_participants_by_mode(mode)
        if not episode.participants_config:
            episode.participants_config = [
                {
                    "id": p.id,
                    "role": p.role,
                    "system_prompt": p.system_prompt,
                    "voice_id": p.voice_id
                }
                for p in participants
            ]
            episode.save(update_fields=['participants_config', 'updated_at'])

        # 加载现有对话
        dialogue_entries = [dict(item) for item in (episode.dialogue or [])]

        # 确定下一发言人（轮询：judge -> llm1 -> llm2 -> judge）
        participant_order = ['judge', 'llm1', 'llm2'] if mode == 'debate' else ['tutor', 'student1', 'student2']

        # 根据最后的发言者确定下一个
        last_speaker = dialogue_entries[-1].get('participant') if dialogue_entries else None
        if last_speaker in participant_order:
            last_idx = participant_order.index(last_speaker)
            next_idx = (last_idx + 1) % len(participant_order)
        else:
            # 如果最后一个是user或其他，选择第一个非主持人
            next_idx = 1 if len(participant_order) > 1 else 0

        next_speaker_id = participant_order[next_idx]
        next_speaker = next(p for p in participants if p.id == next_speaker_id)

        # 构建上下文（最近的几条消息）
        recent_context = "\n\n".join([
            f"{item.get('role', item.get('participant'))}: {item.get('content', '')}"
            for item in dialogue_entries[-5:]  # 最近5条
        ])

        # 生成AI回复
        prompt = (
            f"当前正在讨论：{topic}\n\n"
            f"最近的对话：\n{recent_context}\n\n"
            f"请作为{next_speaker.role}，针对用户的最新发言给出你的观点回应。长度100-200字。"
        )

        client = OpenAI(
            api_key=getattr(settings, 'OPENAI_API_KEY', ''),
            base_url=getattr(settings, 'OPENAI_API_BASE', 'https://api.openai.com/v1')
        )
        model = getattr(settings, 'OPENAI_MODEL', 'moonshot-v1-8k')

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": next_speaker.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()

        # 添加AI回复到对话
        new_entry = {
            'participant': next_speaker_id,
            'role': next_speaker.role,
            'content': content,
            'timestamp': timezone.now().isoformat()
        }
        dialogue_entries.append(new_entry)

        # 更新episode
        episode.dialogue = dialogue_entries
        episode.script = _build_script_from_dialogue(dialogue_entries, participants)
        episode.status = 'published'
        episode.published_at = timezone.now()
        episode.save(update_fields=['dialogue', 'script', 'status', 'published_at', 'updated_at'])

        return f"Debate followup {episode_id} generated successfully"

    except Exception as e:
        print(f"Failed to generate debate followup for episode {episode_id}: {e}")
        if episode:
            episode.status = 'failed'
            episode.generation_error = str(e)[:1000]
            episode.save(update_fields=['status', 'generation_error', 'updated_at'])
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
