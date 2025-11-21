"""
音频处理工具
使用 pydub 处理音频文件
"""
from pydub import AudioSegment
import os
import subprocess
import tempfile


def get_audio_duration(file_path):
    """获取音频时长（秒）"""
    try:
        audio = AudioSegment.from_file(file_path)
        return int(len(audio) / 1000)
    except Exception as e:
        raise Exception(f"无法读取音频文件: {str(e)}")


def process_audio(input_path, output_path=None):
    """
    处理音频文件：
    1. 转换为 MP3
    2. 标准化音量
    3. 统一码率（192kbps）

    参数:
        input_path: 输入文件路径
        output_path: 输出文件路径（可选，默认覆盖原文件）

    返回:
        dict: {
            'success': bool,
            'duration': int (秒),
            'file_size': int (字节),
            'error': str (如果失败)
        }
    """
    try:
        # 加载音频（支持多种格式，包括从视频文件中提取音频）
        try:
            audio = AudioSegment.from_file(input_path)
        except Exception as e:
            # 如果失败（通常是因为文件包含视频流或格式特殊），使用 ffmpeg 直接提取音频
            error_msg = str(e)
            if "4GB" in error_msg or "video" in error_msg.lower() or "Unable to process" in error_msg:
                # 使用 ffmpeg 提取音频流到临时文件
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_path = temp_file.name

                try:
                    # ffmpeg 命令：提取音频流，不重新编码
                    subprocess.run([
                        'ffmpeg', '-i', input_path,
                        '-vn',  # 不包含视频
                        '-acodec', 'libmp3lame',  # 使用 MP3 编码
                        '-ab', '192k',  # 比特率
                        '-y',  # 覆盖输出文件
                        temp_path
                    ], check=True, capture_output=True, text=True)

                    # 从临时文件加载音频
                    audio = AudioSegment.from_mp3(temp_path)

                    # 清理临时文件
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except subprocess.CalledProcessError as ffmpeg_error:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise Exception(f"ffmpeg 提取音频失败: {ffmpeg_error.stderr}")
            else:
                raise

        # 标准化音量（防止过大或过小）
        audio = audio.normalize()

        # 如果没有指定输出路径，使用临时文件
        if output_path is None:
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}_processed.mp3"

        # 导出为 MP3（192kbps）
        audio.export(
            output_path,
            format='mp3',
            bitrate='192k',
            parameters=['-q:a', '2']  # VBR quality
        )

        # 获取时长（秒）
        duration = int(len(audio) / 1000)

        # 获取文件大小
        file_size = os.path.getsize(output_path)

        return {
            'success': True,
            'duration': duration,
            'file_size': file_size,
            'output_path': output_path
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def validate_audio_file(file_path, max_size_mb=500):
    """
    验证音频文件

    参数:
        file_path: 文件路径
        max_size_mb: 最大文件大小（MB）

    返回:
        dict: {'valid': bool, 'error': str}
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return {'valid': False, 'error': '文件不存在'}

    # 检查文件大小
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return {'valid': False, 'error': f'文件太大（最大 {max_size_mb}MB）'}

    # 尝试读取音频
    try:
        audio = AudioSegment.from_file(file_path)
        duration = len(audio) / 1000

        # 检查时长（至少1秒，最多12小时）
        if duration < 1:
            return {'valid': False, 'error': '音频太短（至少1秒）'}
        if duration > 12 * 3600:
            return {'valid': False, 'error': '音频太长（最多12小时）'}

        return {'valid': True}
    except Exception as e:
        return {'valid': False, 'error': f'无效的音频文件: {str(e)}'}
