"""
AI 对话 API（Mock 数据）
"""
from fastapi import APIRouter
from app.schemas.conversation import (
    ConversationCreate, MessageCreate, MessageResponse,
    ConversationResponse, ConversationDetail
)
from datetime import datetime
import uuid
from typing import List

router = APIRouter()

# Mock 数据存储
mock_conversations = {}
mock_messages = {}


@router.post("", response_model=ConversationResponse)
async def create_conversation(conv: ConversationCreate):
    """创建对话会话"""
    conv_id = str(uuid.uuid4())
    conversation = ConversationResponse(
        id=conv_id,
        title=conv.topic[:50],
        topic=conv.topic,
        style=conv.style,
        status="active",
        message_count=0,
        created_at=datetime.utcnow()
    )
    mock_conversations[conv_id] = conversation
    mock_messages[conv_id] = []
    return conversation


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: str, message: MessageCreate):
    """发送消息（AI 回复 Mock）"""
    # 保存用户消息
    user_msg = MessageResponse(
        id=str(uuid.uuid4()),
        role="user",
        content=message.content,
        created_at=datetime.utcnow()
    )
    if conversation_id not in mock_messages:
        mock_messages[conversation_id] = []
    mock_messages[conversation_id].append(user_msg)

    # Mock AI 回复（用 xxxxx 占位）
    ai_msg = MessageResponse(
        id=str(uuid.uuid4()),
        role="assistant",
        content="xxxxx xxxxx xxxxx xxxxx xxxxx",
        created_at=datetime.utcnow()
    )
    mock_messages[conversation_id].append(ai_msg)

    # 更新对话计数
    if conversation_id in mock_conversations:
        mock_conversations[conversation_id].message_count += 2

    return ai_msg


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str):
    """获取对话详情"""
    if conversation_id not in mock_conversations:
        conv = ConversationResponse(
            id=conversation_id,
            title="Mock 对话",
            topic="AI 话题",
            style="educational",
            status="active",
            message_count=2,
            created_at=datetime.utcnow()
        )
    else:
        conv = mock_conversations[conversation_id]

    messages = mock_messages.get(conversation_id, [
        MessageResponse(
            id=str(uuid.uuid4()),
            role="user",
            content="你好，请帮我生成播客脚本",
            created_at=datetime.utcnow()
        ),
        MessageResponse(
            id=str(uuid.uuid4()),
            role="assistant",
            content="xxxxx xxxxx xxxxx xxxxx",
            created_at=datetime.utcnow()
        )
    ])

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        topic=conv.topic,
        style=conv.style,
        status=conv.status,
        message_count=conv.message_count,
        created_at=conv.created_at,
        messages=messages,
        total_tokens=1500,
        total_cost=0.05
    )


@router.get("", response_model=List[ConversationResponse])
async def list_conversations():
    """获取对话列表"""
    if mock_conversations:
        return list(mock_conversations.values())

    return [
        ConversationResponse(
            id=str(uuid.uuid4()),
            title="AI 技术讨论",
            topic="人工智能的最新进展",
            style="educational",
            status="completed",
            message_count=6,
            created_at=datetime.utcnow()
        ),
        ConversationResponse(
            id=str(uuid.uuid4()),
            title="区块链技术",
            topic="区块链的应用场景",
            style="casual",
            status="active",
            message_count=4,
            created_at=datetime.utcnow()
        )
    ]


@router.post("/{conversation_id}/finalize")
async def finalize_conversation(conversation_id: str):
    """确认生成脚本"""
    script_id = str(uuid.uuid4())
    return {
        "script_id": script_id,
        "content": "【大牛】xxxxx xxxxx xxxxx\n\n【一帆】xxxxx xxxxx xxxxx",
        "message": "脚本已生成"
    }
