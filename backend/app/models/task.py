"""
Task 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EngineType(str, enum.Enum):
    DIRECT = "direct"
    MOFA = "mofa"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id"), nullable=False, index=True)

    # 生成配置
    voice_config = Column(JSON, nullable=False)  # {"daniu": "voice_id_1", "yifan": "voice_id_2"}
    engine_type = Column(Enum(EngineType), default=EngineType.DIRECT, nullable=False)

    # 任务状态
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    error_message = Column(Text, nullable=True)

    # 成本计费
    credit_cost = Column(Integer, nullable=True)
    chars_processed = Column(Integer, nullable=True)

    # 时间追踪
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 重试逻辑
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=1, nullable=False)

    # 关系
    user = relationship("User", back_populates="tasks")
    script = relationship("Script", back_populates="tasks")
    audios = relationship("Audio", back_populates="task", cascade="all, delete-orphan")
