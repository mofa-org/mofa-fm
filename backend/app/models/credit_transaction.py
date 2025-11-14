"""
CreditTransaction 模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    SCRIPT_GENERATION = "script_generation"
    AUDIO_GENERATION = "audio_generation"
    REFUND = "refund"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # 交易信息
    amount = Column(Integer, nullable=False)  # 正数=充值，负数=消费
    balance_after = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # 关联的 task_id 或 conversation_id
    description = Column(String(500), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = relationship("User", back_populates="credit_transactions")
