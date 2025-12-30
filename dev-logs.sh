#!/bin/bash
# MoFA FM 本地开发环境日志查看

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_DIR/.dev-pids"

SERVICE=$1

if [ -z "$SERVICE" ]; then
    echo "用法: ./dev-logs.sh [django|celery|frontend|all]"
    echo ""
    echo "示例:"
    echo "  ./dev-logs.sh django    - 查看 Django 日志"
    echo "  ./dev-logs.sh celery    - 查看 Celery 日志"
    echo "  ./dev-logs.sh frontend  - 查看前端日志"
    echo "  ./dev-logs.sh all       - 同时查看所有日志"
    exit 1
fi

case $SERVICE in
    django)
        echo -e "${GREEN}=== Django 日志 ===${NC}"
        tail -f "$PID_DIR/django.log"
        ;;
    celery)
        echo -e "${GREEN}=== Celery 日志 ===${NC}"
        tail -f "$PID_DIR/celery.log"
        ;;
    frontend)
        echo -e "${GREEN}=== 前端日志 ===${NC}"
        tail -f "$PID_DIR/frontend.log"
        ;;
    all)
        echo -e "${GREEN}=== 所有服务日志 ===${NC}"
        tail -f "$PID_DIR/django.log" "$PID_DIR/celery.log" "$PID_DIR/frontend.log"
        ;;
    *)
        echo -e "${RED}未知服务: $SERVICE${NC}"
        echo "可用服务: django, celery, frontend, all"
        exit 1
        ;;
esac
