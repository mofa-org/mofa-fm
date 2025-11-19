"""
播客Celery任务
"""
from celery import shared_task
from django.utils import timezone
import os
from utils.audio_processor import process_audio, get_audio_duration


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
def generate_podcast_task(episode_id, script_content):
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
        
        # Generate
        generator.generate(script_content, full_path)
        
        # Update episode
        episode.audio_file.name = relative_path
        episode.status = 'published' 
        episode.duration = int(AudioSegment.from_mp3(full_path).duration_seconds)
        episode.file_size = os.path.getsize(full_path)
        episode.save()
        
    except Exception as e:
        print(f"Failed to generate podcast for episode {episode_id}: {e}")
        if episode: # Only update status if episode object was successfully retrieved
            episode.status = 'failed'
            episode.save()
        raise

