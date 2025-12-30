#!/bin/bash
# MoFA FM 本地开发环境启动脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_DIR="$PROJECT_DIR/.dev-pids"

# 创建 PID 目录
mkdir -p "$PID_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MoFA FM 开发环境启动${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Redis
echo -e "${YELLOW}[1/4] 检查 Redis...${NC}"
if pgrep -x redis-server > /dev/null; then
    echo -e "${GREEN}✓ Redis 已在运行${NC}"
else
    echo -e "${YELLOW}→ 启动 Redis...${NC}"
    redis-server --daemonize yes
    echo -e "${GREEN}✓ Redis 已启动${NC}"
fi
echo ""

# 启动 Django
echo -e "${YELLOW}[2/4] 启动 Django 后端...${NC}"
cd "$BACKEND_DIR"
source venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8000 > "$PID_DIR/django.log" 2>&1 &
echo $! > "$PID_DIR/django.pid"
echo -e "${GREEN}✓ Django 已启动 (PID: $(cat $PID_DIR/django.pid))${NC}"
echo -e "  日志: $PID_DIR/django.log"
echo ""

# 启动 Celery Worker
echo -e "${YELLOW}[3/4] 启动 Celery Worker...${NC}"
cd "$BACKEND_DIR"
nohup celery -A config worker --loglevel=info > "$PID_DIR/celery.log" 2>&1 &
echo $! > "$PID_DIR/celery.pid"
echo -e "${GREEN}✓ Celery Worker 已启动 (PID: $(cat $PID_DIR/celery.pid))${NC}"
echo -e "  日志: $PID_DIR/celery.log"
echo ""

# 启动前端
echo -e "${YELLOW}[4/4] 启动前端开发服务器...${NC}"
cd "$FRONTEND_DIR"
nohup npm run dev > "$PID_DIR/frontend.log" 2>&1 &
echo $! > "$PID_DIR/frontend.pid"
echo -e "${GREEN}✓ 前端已启动 (PID: $(cat $PID_DIR/frontend.pid))${NC}"
echo -e "  日志: $PID_DIR/frontend.log"
echo ""

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 3

# 检查服务状态
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  后端 API: ${GREEN}http://localhost:8000/api${NC}"
echo -e "  前端界面: ${GREEN}http://localhost:5173${NC}"
echo -e "  管理后台: ${GREEN}http://localhost:8000/admin${NC}"
echo ""
echo -e "${YELLOW}查看日志:${NC}"
echo -e "  Django:  tail -f $PID_DIR/django.log"
echo -e "  Celery:  tail -f $PID_DIR/celery.log"
echo -e "  前端:    tail -f $PID_DIR/frontend.log"
echo ""
echo -e "${YELLOW}停止服务:${NC}"
echo -e "  运行: ./dev-stop.sh"
echo ""
