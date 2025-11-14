"""
脚本相关 Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScriptCreate(BaseModel):
    title: Optional[str] = None
    content: str
    source: str = "uploaded"


class ScriptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ScriptResponse(BaseModel):
    id: str
    title: Optional[str]
    content: str
    source: str
    estimated_chars: int
    estimated_duration: float
    created_at: datetime

    class Config:
        from_attributes = True
