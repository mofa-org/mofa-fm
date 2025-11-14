"""
FastAPI 主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, conversations, scripts, tasks

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["AI对话"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["脚本管理"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["音频任务"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
