#!/bin/bash
# MoFA FM 本地开发环境停止脚本

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_DIR/.dev-pids"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  停止 MoFA FM 开发环境${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 停止 Django
if [ -f "$PID_DIR/django.pid" ]; then
    PID=$(cat "$PID_DIR/django.pid")
    if kill -0 $PID 2>/dev/null; then
        echo -e "${YELLOW}停止 Django (PID: $PID)...${NC}"
        kill $PID
        rm "$PID_DIR/django.pid"
        echo -e "${GREEN}✓ Django 已停止${NC}"
    else
        echo -e "${RED}✗ Django 进程不存在${NC}"
        rm "$PID_DIR/django.pid"
    fi
else
    echo -e "${YELLOW}→ Django 未运行${NC}"
fi

# 停止 Celery
if [ -f "$PID_DIR/celery.pid" ]; then
    PID=$(cat "$PID_DIR/celery.pid")
    if kill -0 $PID 2>/dev/null; then
        echo -e "${YELLOW}停止 Celery Worker (PID: $PID)...${NC}"
        kill $PID
        # Celery 可能有子进程，强制杀掉所有 celery 进程
        pkill -f "celery -A config worker" || true
        rm "$PID_DIR/celery.pid"
        echo -e "${GREEN}✓ Celery Worker 已停止${NC}"
    else
        echo -e "${RED}✗ Celery 进程不存在${NC}"
        rm "$PID_DIR/celery.pid"
    fi
else
    echo -e "${YELLOW}→ Celery 未运行${NC}"
fi

# 停止前端
if [ -f "$PID_DIR/frontend.pid" ]; then
    PID=$(cat "$PID_DIR/frontend.pid")
    if kill -0 $PID 2>/dev/null; then
        echo -e "${YELLOW}停止前端 (PID: $PID)...${NC}"
        kill $PID
        # 前端可能有子进程（vite）
        pkill -f "vite" || true
        rm "$PID_DIR/frontend.pid"
        echo -e "${GREEN}✓ 前端已停止${NC}"
    else
        echo -e "${RED}✗ 前端进程不存在${NC}"
        rm "$PID_DIR/frontend.pid"
    fi
else
    echo -e "${YELLOW}→ 前端未运行${NC}"
fi

# Redis 保持运行（可能被其他项目使用）
echo -e "${YELLOW}→ Redis 保持运行（如需停止请手动执行: redis-cli shutdown）${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  所有服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
