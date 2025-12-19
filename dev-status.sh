#!/bin/bash
# MoFA FM 本地开发环境状态检查

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_DIR/.dev-pids"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  MoFA FM 开发环境状态${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 检查 Redis
if pgrep -x redis-server > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Redis: ${GREEN}运行中${NC}"
else
    echo -e "  ${RED}✗${NC} Redis: ${RED}未运行${NC}"
fi

# 检查 Django
if [ -f "$PID_DIR/django.pid" ] && kill -0 $(cat "$PID_DIR/django.pid") 2>/dev/null; then
    PID=$(cat "$PID_DIR/django.pid")
    echo -e "  ${GREEN}✓${NC} Django: ${GREEN}运行中${NC} (PID: $PID)"
    echo -e "    URL: http://localhost:8000"
else
    echo -e "  ${RED}✗${NC} Django: ${RED}未运行${NC}"
fi

# 检查 Celery
if [ -f "$PID_DIR/celery.pid" ] && kill -0 $(cat "$PID_DIR/celery.pid") 2>/dev/null; then
    PID=$(cat "$PID_DIR/celery.pid")
    echo -e "  ${GREEN}✓${NC} Celery: ${GREEN}运行中${NC} (PID: $PID)"
else
    echo -e "  ${RED}✗${NC} Celery: ${RED}未运行${NC}"
fi

# 检查前端
if [ -f "$PID_DIR/frontend.pid" ] && kill -0 $(cat "$PID_DIR/frontend.pid") 2>/dev/null; then
    PID=$(cat "$PID_DIR/frontend.pid")
    echo -e "  ${GREEN}✓${NC} 前端: ${GREEN}运行中${NC} (PID: $PID)"
    echo -e "    URL: http://localhost:5173"
else
    echo -e "  ${RED}✗${NC} 前端: ${RED}未运行${NC}"
fi

echo ""
