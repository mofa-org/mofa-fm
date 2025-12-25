#!/bin/bash
# Docker 镜像构建脚本

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="mofa-fm/dora-runtime:latest"

echo "============================================"
echo "🐳 构建 Dora Runtime Docker 镜像"
echo "============================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装 Docker"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

# 检查 Docker daemon
if ! docker info &> /dev/null; then
    echo "❌ 错误: Docker daemon 未运行"
    echo "请启动 Docker Desktop 或 Docker 服务"
    exit 1
fi

# 显示构建信息
echo "镜像名称: $IMAGE_NAME"
echo "构建目录: $SCRIPT_DIR"
echo ""
echo "⚠️  注意: 构建过程可能需要 5-10 分钟"
echo "   - 下载基础镜像"
echo "   - 安装 Dora CLI"
echo "   - 安装 Python 依赖"
echo ""

read -rp "是否继续构建？(Y/n) " confirm
confirm=${confirm:-Y}
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "已取消构建"
    exit 0
fi

echo ""
echo "🚀 开始构建..."
echo ""

# 构建镜像
cd "$SCRIPT_DIR"
docker build \
    --tag "$IMAGE_NAME" \
    --file Dockerfile \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ Docker 镜像构建成功！"
    echo "============================================"
    echo ""
    echo "镜像信息:"
    docker images "$IMAGE_NAME"
    echo ""
    echo "使用方法:"
    echo "  cd examples/chatbot-openai-0905"
    echo "  ./docker-start.sh"
    echo ""
else
    echo ""
    echo "❌ Docker 镜像构建失败"
    exit 1
fi
