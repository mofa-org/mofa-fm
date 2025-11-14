"""
对话相关 Schemas
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ConversationCreate(BaseModel):
    topic: str
    style: str  # educational/casual/interview
    target_duration: int
    speakers: List[str]


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    topic: str
    style: str
    status: str
    message_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse]
    total_tokens: int
    total_cost: float
