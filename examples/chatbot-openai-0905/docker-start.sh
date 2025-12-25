#!/bin/bash
# Chatbot OpenAI Docker 启动脚本
# 自动处理 Docker 环境，用户无感知

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMAGE_NAME="mofa-fm/dora-runtime:latest"

echo "============================================"
echo "🐳 Docker 模式启动 Chatbot OpenAI"
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

# 检查 OPENAI_API_KEY
if [ -z "${OPENAI_API_KEY:-}" ]; then
    read -rsp "请输入 OPENAI_API_KEY: " OPENAI_API_KEY
    echo ""
fi

if [ -z "${OPENAI_API_KEY}" ]; then
    echo "❌ 错误: OPENAI_API_KEY 不能为空"
    exit 1
fi

echo "✅ API Key 已设置（长度: ${#OPENAI_API_KEY}）"
echo ""

# 检查镜像是否存在
if ! docker images | grep -q "mofa-fm/dora-runtime"; then
    echo "📥 Docker 镜像不存在，开始构建..."
    echo "   这可能需要 10-20 分钟（仅首次运行）"
    echo ""

    cd "$REPO_ROOT"
    docker build -t "$IMAGE_NAME" .

    if [ $? -ne 0 ]; then
        echo "❌ Docker 镜像构建失败"
        exit 1
    fi

    echo ""
    echo "✅ Docker 镜像构建成功"
    echo ""
fi

# 查找 Dora 主仓库路径（用于挂载 Rust 二进制文件）
DORA_BINS_DIR=""
if [ -d "$HOME/dora/target/release" ]; then
    DORA_BINS_DIR="$HOME/dora/target/release"
elif [ -d "$REPO_ROOT/../../dora/target/release" ]; then
    DORA_BINS_DIR="$(cd "$REPO_ROOT/../../dora/target/release" && pwd)"
fi

if [ -z "$DORA_BINS_DIR" ]; then
    echo "⚠️  警告: 未找到 Dora Rust 二进制文件目录"
    echo "   将使用镜像内置的 dora CLI"
    echo "   如需完整功能，请先编译 Dora 主仓库："
    echo "   cd /path/to/dora && cargo build --release"
    echo ""
    read -rp "是否继续？(y/N) " continue_choice
    continue_choice=${continue_choice:-N}
    if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# 准备 Docker 运行参数
DOCKER_ARGS=(
    "--rm"
    "-it"
    "-v" "$SCRIPT_DIR:/workspace"
    "-v" "$HOME/.dora/models:/root/.dora/models"
    "-e" "OPENAI_API_KEY=$OPENAI_API_KEY"
    "-e" "SPAWN_MAAS=0"
    "-e" "LANG=zh_CN.UTF-8"
    "-e" "LC_ALL=zh_CN.UTF-8"
    "-p" "8123:8123"
    "--workdir" "/workspace"
)

# 如果找到了 Rust 二进制文件，挂载它们
if [ -n "$DORA_BINS_DIR" ]; then
    DOCKER_ARGS+=("-v" "$DORA_BINS_DIR:/usr/local/bin/dora-bins")
    DOCKER_ARGS+=("-e" "PATH=/usr/local/bin/dora-bins:/usr/local/bin:/root/.cargo/bin:/usr/bin:/bin")
    echo "✅ 已挂载 Rust 二进制文件: $DORA_BINS_DIR"
fi

# 检查 GPU 支持
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    DOCKER_ARGS+=("--gpus" "all")
    echo "✅ 检测到 NVIDIA GPU，已启用 GPU 支持"
fi

echo ""
echo "🚀 启动 Docker 容器..."
echo ""

# 运行容器
docker run "${DOCKER_ARGS[@]}" "$IMAGE_NAME" bash -c '
    set -e

    echo "📋 检查环境..."
    echo "  • Python: $(python --version)"
    echo "  • Dora: $(dora --version 2>&1 || echo "未安装")"
    echo ""

    echo "🔧 启动 dora daemon..."
    dora up &
    DORA_PID=$!
    sleep 3

    echo "✅ Dora daemon 已启动 (PID: $DORA_PID)"
    echo ""

    echo "📦 启动 dataflow..."
    DATAFLOW_UUID=$(dora start chatbot-staticflow.yml --detach 2>&1 | grep "dataflow started:" | awk "{print \$3}")
    echo "  • Dataflow UUID: ${DATAFLOW_UUID:-<未知>}"
    echo "  • 等待节点启动（包括 TTS 模型加载）..."
    sleep 15

    echo ""
    echo "📊 Dataflow 状态:"
    dora list
    echo ""

    echo "🌐 启动 WebSocket 服务器..."
    echo "  • 监听地址: 0.0.0.0:8123"
    echo ""
    echo "============================================"
    echo "✅ 系统启动完成！"
    echo "============================================"
    echo ""
    echo "连接信息："
    echo "  • WebSocket: ws://localhost:8123"
    echo ""
    echo "提示："
    echo "  • 使用浏览器或客户端连接 WebSocket"
    echo "  • 按 Ctrl+C 停止服务"
    echo ""

    trap "echo \"\\n🛑 正在停止服务...\"; kill $DORA_PID 2>/dev/null || true; exit 0" INT TERM

    # 启动 WebSocket 服务器（前台运行）
    SPAWN_MAAS=0 dora-openai-websocket --name wserver || \
    dora-text-websocket --name wserver || \
    echo "⚠️  警告: WebSocket 服务器启动失败，请检查二进制文件"

    wait
'

echo ""
echo "👋 容器已退出"
