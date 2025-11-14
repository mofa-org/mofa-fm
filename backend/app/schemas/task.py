"""
任务相关 Schemas
"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class TaskCreate(BaseModel):
    script_id: str
    voice_config: Dict[str, str]  # {"daniu": "voice_id_1", "yifan": "voice_id_2"}


class AudioResponse(BaseModel):
    id: str
    format: str
    file_path: str
    file_size: int
    duration: float
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: str
    status: str
    progress: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class TaskDetail(TaskResponse):
    script_id: str
    voice_config: Dict[str, str]
    credit_cost: Optional[int]
    chars_processed: Optional[int]
    audios: List[AudioResponse]


class VoiceInfo(BaseModel):
    voice_id: str
    display_name: str
    preview_url: Optional[str]
    language: str = "zh"
    category: str = "general"
