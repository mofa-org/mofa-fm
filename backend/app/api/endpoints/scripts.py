"""
脚本管理 API（Mock 数据）
"""
from fastapi import APIRouter
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptResponse
from datetime import datetime
import uuid
from typing import List

router = APIRouter()

# Mock 数据存储
mock_scripts = {}


@router.post("", response_model=ScriptResponse)
async def create_script(script: ScriptCreate):
    """创建/上传脚本"""
    script_id = str(uuid.uuid4())
    estimated_chars = len(script.content)
    estimated_duration = estimated_chars / 4.5  # 约 4.5 字/秒

    response = ScriptResponse(
        id=script_id,
        title=script.title or "未命名脚本",
        content=script.content,
        source=script.source,
        estimated_chars=estimated_chars,
        estimated_duration=estimated_duration,
        created_at=datetime.utcnow()
    )
    mock_scripts[script_id] = response
    return response


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(script_id: str):
    """获取脚本详情"""
    if script_id in mock_scripts:
        return mock_scripts[script_id]

    return ScriptResponse(
        id=script_id,
        title="示例脚本",
        content="【大牛】xxxxx xxxxx xxxxx xxxxx\n\n【一帆】xxxxx xxxxx xxxxx xxxxx\n\n【大牛】xxxxx xxxxx\n\n【一帆】xxxxx xxxxx",
        source="ai_generated",
        estimated_chars=100,
        estimated_duration=22.2,
        created_at=datetime.utcnow()
    )


@router.get("", response_model=List[ScriptResponse])
async def list_scripts():
    """获取脚本列表"""
    if mock_scripts:
        return list(mock_scripts.values())

    return [
        ScriptResponse(
            id=str(uuid.uuid4()),
            title="AI 技术讨论",
            content="【大牛】xxxxx xxxxx xxxxx\n\n【一帆】xxxxx xxxxx",
            source="ai_generated",
            estimated_chars=150,
            estimated_duration=33.3,
            created_at=datetime.utcnow()
        ),
        ScriptResponse(
            id=str(uuid.uuid4()),
            title="产品设计思路",
            content="【大牛】xxxxx xxxxx\n\n【一帆】xxxxx xxxxx xxxxx",
            source="uploaded",
            estimated_chars=200,
            estimated_duration=44.4,
            created_at=datetime.utcnow()
        )
    ]


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(script_id: str, update: ScriptUpdate):
    """更新脚本"""
    if script_id in mock_scripts:
        existing = mock_scripts[script_id]
        if update.title:
            existing.title = update.title
        if update.content:
            existing.content = update.content
            existing.estimated_chars = len(update.content)
            existing.estimated_duration = len(update.content) / 4.5
        return existing

    return ScriptResponse(
        id=script_id,
        title=update.title or "更新后的脚本",
        content=update.content or "【大牛】xxxxx\n\n【一帆】xxxxx",
        source="uploaded",
        estimated_chars=50,
        estimated_duration=11.1,
        created_at=datetime.utcnow()
    )
