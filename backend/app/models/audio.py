"""
Audio 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class AudioFormat(str, enum.Enum):
    WAV = "wav"
    MP3 = "mp3"


class Audio(Base):
    __tablename__ = "audios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)

    # 文件信息
    format = Column(Enum(AudioFormat), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # 字节
    duration = Column(Float, nullable=False)  # 秒
    sample_rate = Column(Integer, default=32000, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # 永久保留则为 null

    # 关系
    task = relationship("Task", back_populates="audios")
