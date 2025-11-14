"""
Script 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ScriptSource(str, enum.Enum):
    UPLOADED = "uploaded"
    AI_GENERATED = "ai_generated"
    TEMPLATE = "template"


class Script(Base):
    __tablename__ = "scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)

    # 脚本内容
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)

    # 来源
    source = Column(Enum(ScriptSource), nullable=False)
    generation_params = Column(JSON, nullable=True)  # AI 生成参数

    # 统计
    estimated_chars = Column(Integer, nullable=False, default=0)
    estimated_duration = Column(Float, nullable=False, default=0.0)  # 秒

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="scripts")
    conversation = relationship("Conversation", back_populates="script")
    tasks = relationship("Task", back_populates="script", cascade="all, delete-orphan")
