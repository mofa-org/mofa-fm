"""
认证 API（Mock 数据）
"""
from fastapi import APIRouter, HTTPException
from app.schemas.auth import UserRegister, UserLogin, Token, UserProfile
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/register", response_model=UserProfile)
async def register(user: UserRegister):
    """用户注册"""
    return UserProfile(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        credit_balance=1000,
        status="active",
        created_at=datetime.utcnow().isoformat()
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """用户登录"""
    # Mock token
    return Token(access_token="mock_jwt_token_" + str(uuid.uuid4())[:8])


@router.get("/profile", response_model=UserProfile)
async def get_profile():
    """获取当前用户信息"""
    return UserProfile(
        id=str(uuid.uuid4()),
        username="demo_user",
        email="demo@example.com",
        credit_balance=1000,
        status="active",
        created_at=datetime.utcnow().isoformat()
    )
