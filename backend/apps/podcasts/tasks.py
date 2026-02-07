"""
播客Celery任务
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import os
from utils.audio_processor import process_audio


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

def _set_episode_generation_state(
    episode,
    *,
    status_value=None,
    stage_value=None,
    error_value=None,
):
    update_fields = []
    if status_value is not None and episode.status != status_value:
        episode.status = status_value
        update_fields.append('status')
    if stage_value is not None and episode.generation_stage != stage_value:
        episode.generation_stage = stage_value
        update_fields.append('generation_stage')
    if error_value is not None and episode.generation_error != error_value:
        episode.generation_error = error_value
        update_fields.append('generation_error')
    if update_fields:
        update_fields.append('updated_at')
        episode.save(update_fields=update_fields)


def _publish_generated_episode(episode, script_content):
    from .services.generator import PodcastGenerator
    from pydub import AudioSegment
    from django.conf import settings
    from .services.cover_ai import generate_episode_cover

    _set_episode_generation_state(
        episode,
        status_value='processing',
        stage_value='audio_generating',
        error_value='',
    )

    generator = PodcastGenerator()

    filename = f"generated_{episode.slug}_{episode.id}.mp3"
    relative_path = f"episodes/{episode.created_at.strftime('%Y/%m')}/{filename}"
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    # 清理占位文件，避免残留空文件
    placeholder_name = episode.audio_file.name
    if placeholder_name and placeholder_name != relative_path:
        storage = episode.audio_file.storage
        if storage.exists(placeholder_name):
            storage.delete(placeholder_name)

    generator.generate(script_content, full_path)

    episode.audio_file.name = relative_path
    episode.script = script_content
    episode.status = 'published'
    episode.generation_stage = 'cover_generating'
    episode.generation_error = ''
    episode.duration = int(AudioSegment.from_mp3(full_path).duration_seconds)
    episode.file_size = os.path.getsize(full_path)
    episode.published_at = timezone.now()
    episode.save(
        update_fields=[
            'audio_file',
            'script',
            'status',
            'generation_stage',
            'generation_error',
            'duration',
            'file_size',
            'published_at',
            'updated_at',
        ]
    )

    # 封面失败不阻断发布
    try:
        generate_episode_cover(episode)
    except Exception as cover_exc:
        print(f"Failed to generate cover for episode {episode.id}: {cover_exc}")

    _set_episode_generation_state(
        episode,
        status_value='published',
        stage_value='completed',
        error_value='',
    )

    if episode.show_id:
        show = episode.show
        show.episodes_count = show.episodes.filter(status='published').count()
        show.save(update_fields=['episodes_count', 'updated_at'])


@shared_task
def generate_podcast_task(episode_id, script_content):
    """
    Background task to generate podcast audio from script.
    """
    from .models import Episode

    episode = None
    try:
        episode = Episode.objects.get(id=episode_id)
        _publish_generated_episode(episode=episode, script_content=script_content)
    except Exception as e:
        print(f"Failed to generate podcast for episode {episode_id}: {e}")
        if episode:
            _set_episode_generation_state(
                episode,
                status_value='failed',
                stage_value='failed',
                error_value=str(e)[:1000],
            )
        raise


@shared_task
def generate_source_podcast_task(episode_id, source_url, max_items=8, template='news_flash'):
    """
    Background task to generate podcast from source URL (RSS/webpage).
    """
    from .models import Episode
    from .services.source_ingest import collect_source_material, generate_script_from_material

    episode = None
    try:
        episode = Episode.objects.get(id=episode_id)
        _set_episode_generation_state(
            episode,
            status_value='processing',
            stage_value='source_fetching',
            error_value='',
        )

        material = collect_source_material(source_url=source_url, max_items=max_items)

        _set_episode_generation_state(
            episode,
            status_value='processing',
            stage_value='script_generating',
        )
        script = generate_script_from_material(material, template=template)

        meta = dict(episode.generation_meta or {})
        meta.update({
            "type": material.get("source_type") or "source",
            "source_url": source_url,
            "max_items": max_items,
            "template": template,
            "source_title": material.get("source_title") or "",
            "item_count": len(material.get("items") or []),
        })

        if meta.get("auto_title"):
            source_title = material.get("source_title") or "来源内容"
            episode.title = f"{source_title} 快报"

        episode.script = script
        episode.generation_meta = meta
        episode.save(update_fields=['title', 'script', 'generation_meta', 'updated_at'])

        _publish_generated_episode(episode=episode, script_content=script)
    except Exception as e:
        print(f"Failed to generate source podcast for episode {episode_id}: {e}")
        if episode:
            _set_episode_generation_state(
                episode,
                status_value='failed',
                stage_value='failed',
                error_value=str(e)[:1000],
            )
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
