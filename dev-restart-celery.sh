#!/bin/bash
# 快速重启 Celery Worker（用于 AI 功能开发）

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
PID_DIR="$PROJECT_DIR/.dev-pids"

echo -e "${YELLOW}🔄 重启 Celery Worker...${NC}"

# 停止旧的 Celery
if [ -f "$PID_DIR/celery.pid" ]; then
    OLD_PID=$(cat "$PID_DIR/celery.pid")
    if kill -0 $OLD_PID 2>/dev/null; then
        kill $OLD_PID
        pkill -f "celery -A config worker" || true
        echo -e "${GREEN}✓ 已停止旧的 Celery Worker${NC}"
    fi
fi

# 启动新的 Celery
cd "$BACKEND_DIR"
source venv/bin/activate
nohup celery -A config worker --loglevel=info > "$PID_DIR/celery.log" 2>&1 &
echo $! > "$PID_DIR/celery.pid"

sleep 2

if kill -0 $(cat "$PID_DIR/celery.pid") 2>/dev/null; then
    echo -e "${GREEN}✓ Celery Worker 已重启 (PID: $(cat $PID_DIR/celery.pid))${NC}"
    echo -e "  日志: tail -f $PID_DIR/celery.log"
else
    echo -e "${RED}✗ Celery Worker 启动失败${NC}"
    echo -e "  查看日志: cat $PID_DIR/celery.log"
    exit 1
fi
