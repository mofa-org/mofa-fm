"""
Conversation 和 ConversationMessage 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ConversationStyle(str, enum.Enum):
    EDUCATIONAL = "educational"
    CASUAL = "casual"
    INTERVIEW = "interview"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    script_id = Column(UUID(as_uuid=True), ForeignKey("scripts.id"), nullable=True)

    # 对话元信息
    title = Column(String(255), nullable=True)
    topic = Column(String(500), nullable=False)
    style = Column(Enum(ConversationStyle), nullable=False)
    target_duration = Column(Integer, nullable=False)  # 秒
    speakers = Column(JSON, nullable=False)  # ["大牛", "一帆"]

    # 状态
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="conversations")
    script = relationship("Script", back_populates="conversation", uselist=False)
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)

    # 消息内容
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)

    # AI 元数据
    metadata = Column(JSON, nullable=True)  # model, tokens, cost, latency

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    conversation = relationship("Conversation", back_populates="messages")
