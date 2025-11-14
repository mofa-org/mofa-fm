"""
音频任务 API（Mock 数据）
"""
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import FileResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskDetail, AudioResponse, VoiceInfo
from datetime import datetime
import uuid
import os
import numpy as np
from scipy.io import wavfile
from typing import List
import random

router = APIRouter()

# Mock 数据存储
mock_tasks = {}


def generate_mock_audio(task_id: str, segment_index: int, frequency: int):
    """生成 Mock 音频（不同频率的正弦波）"""
    sample_rate = 32000
    duration = 2.0  # 每段 2 秒
    t = np.linspace(0, duration, int(sample_rate * duration))

    # 不同段落用不同频率
    audio = np.sin(2 * np.pi * frequency * t)
    audio = (audio * 32767).astype(np.int16)

    # 保存文件
    os.makedirs("/tmp/mofa-voice/audio", exist_ok=True)
    file_path = f"/tmp/mofa-voice/audio/{task_id}_{segment_index}.wav"
    wavfile.write(file_path, sample_rate, audio)

    return file_path


@router.post("", response_model=TaskResponse)
async def create_task(task: TaskCreate, background_tasks: BackgroundTasks):
    """创建音频生成任务"""
    task_id = str(uuid.uuid4())

    response = TaskResponse(
        id=task_id,
        status="pending",
        progress=0,
        created_at=datetime.utcnow(),
        started_at=None,
        completed_at=None,
        error_message=None
    )
    mock_tasks[task_id] = response

    # 模拟异步生成音频
    # background_tasks.add_task(simulate_audio_generation, task_id)

    return response


async def simulate_audio_generation(task_id: str):
    """模拟音频生成过程"""
    import asyncio

    # 更新为 processing
    if task_id in mock_tasks:
        mock_tasks[task_id].status = "processing"
        mock_tasks[task_id].started_at = datetime.utcnow()

        # 模拟进度
        for progress in [20, 40, 60, 80, 100]:
            await asyncio.sleep(1)
            mock_tasks[task_id].progress = progress

        # 生成 Mock 音频（2 个片段，不同频率）
        generate_mock_audio(task_id, 0, 440)  # A4 音高（大牛）
        generate_mock_audio(task_id, 1, 554)  # C#5 音高（一帆）

        mock_tasks[task_id].status = "completed"
        mock_tasks[task_id].completed_at = datetime.utcnow()


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(task_id: str):
    """获取任务详情"""
    # 立即返回完成状态（方便测试）
    return TaskDetail(
        id=task_id,
        status="completed",
        progress=100,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        error_message=None,
        script_id=str(uuid.uuid4()),
        voice_config={"daniu": "voice_1", "yifan": "voice_2"},
        credit_cost=50,
        chars_processed=200,
        audios=[
            AudioResponse(
                id=str(uuid.uuid4()),
                format="wav",
                file_path=f"/tmp/mofa-voice/audio/{task_id}_mock.wav",
                file_size=128000,
                duration=10.5,
                created_at=datetime.utcnow()
            ),
            AudioResponse(
                id=str(uuid.uuid4()),
                format="mp3",
                file_path=f"/tmp/mofa-voice/audio/{task_id}_mock.mp3",
                file_size=85000,
                duration=10.5,
                created_at=datetime.utcnow()
            )
        ]
    )


@router.get("", response_model=List[TaskResponse])
async def list_tasks():
    """获取任务列表"""
    if mock_tasks:
        return list(mock_tasks.values())

    return [
        TaskResponse(
            id=str(uuid.uuid4()),
            status="completed",
            progress=100,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error_message=None
        ),
        TaskResponse(
            id=str(uuid.uuid4()),
            status="processing",
            progress=65,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=None,
            error_message=None
        )
    ]


@router.get("/audios/{audio_id}/download")
async def download_audio(audio_id: str):
    """下载音频文件"""
    # 生成临时音频用于下载
    sample_rate = 32000
    duration = 5.0
    t = np.linspace(0, duration, int(sample_rate * duration))

    # 生成不同频率的组合（模拟对话）
    audio1 = np.sin(2 * np.pi * 440 * t[:len(t)//2])  # 大牛段落
    audio2 = np.sin(2 * np.pi * 554 * t[len(t)//2:])  # 一帆段落
    audio = np.concatenate([audio1, audio2])
    audio = (audio * 32767).astype(np.int16)

    file_path = f"/tmp/mofa-voice/audio/{audio_id}.wav"
    os.makedirs("/tmp/mofa-voice/audio", exist_ok=True)
    wavfile.write(file_path, sample_rate, audio)

    return FileResponse(file_path, media_type="audio/wav", filename=f"podcast_{audio_id}.wav")


@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices():
    """获取可用声音列表"""
    return [
        VoiceInfo(
            voice_id="voice_daniu_1",
            display_name="大牛（男声1）",
            preview_url=None,
            language="zh",
            category="male"
        ),
        VoiceInfo(
            voice_id="voice_daniu_2",
            display_name="大牛（男声2）",
            preview_url=None,
            language="zh",
            category="male"
        ),
        VoiceInfo(
            voice_id="voice_yifan_1",
            display_name="一帆（女声1）",
            preview_url=None,
            language="zh",
            category="female"
        ),
        VoiceInfo(
            voice_id="voice_yifan_2",
            display_name="一帆（女声2）",
            preview_url=None,
            language="zh",
            category="female"
        )
    ]
