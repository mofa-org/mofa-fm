"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "MoFA Voice WebApp"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/mofa_voice"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # TTS 引擎配置
    ENGINE_TYPE: str = "direct"  # direct 或 mofa

    # MiniMax API 配置
    MINIMAX_API_KEY: Optional[str] = None

    # OpenAI API 配置
    OPENAI_API_KEY: Optional[str] = None

    # 文件存储
    AUDIO_STORAGE_PATH: str = "/tmp/mofa-voice/audio"
    SCRIPT_STORAGE_PATH: str = "/tmp/mofa-voice/scripts"

    class Config:
        env_file = ".env"


settings = Settings()
