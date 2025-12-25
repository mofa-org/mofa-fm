#!/bin/bash
# Conference Docker 启动脚本
# 支持 debate 和 study 模式

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMAGE_NAME="mofa-fm/dora-runtime:latest"

echo "============================================"
echo "🐳 Docker 模式启动 Conference System"
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

# 选择模式
echo "请选择运行模式:"
echo "  1. Debate (辩论模式 - 3人辩论)"
echo "  2. Study (学习模式 - 群体学习)"
echo ""
read -rp "请选择 (1/2) [1]: " mode_choice
mode_choice=${mode_choice:-1}

case $mode_choice in
    1)
        MODE="debate"
        DATAFLOW="dataflow-debate-sequential.yml"
        ;;
    2)
        MODE="study"
        DATAFLOW="dataflow-study-audio-multi.yml"
        ;;
    *)
        echo "无效选择，使用默认: debate"
        MODE="debate"
        DATAFLOW="dataflow-debate-sequential.yml"
        ;;
esac

echo "✅ 已选择: $MODE 模式"
echo ""

# 检查 API Keys（至少需要一个）
if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ALIBABA_CLOUD_API_KEY:-}" ] && [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "请输入至少一个 API Key（其他可以留空）："
    read -rsp "OPENAI_API_KEY (回车跳过): " OPENAI_API_KEY_INPUT
    echo ""
    read -rsp "ALIBABA_CLOUD_API_KEY (回车跳过): " ALIBABA_CLOUD_API_KEY_INPUT
    echo ""
    read -rsp "DEEPSEEK_API_KEY (回车跳过): " DEEPSEEK_API_KEY_INPUT
    echo ""

    OPENAI_API_KEY="${OPENAI_API_KEY_INPUT:-}"
    ALIBABA_CLOUD_API_KEY="${ALIBABA_CLOUD_API_KEY_INPUT:-}"
    DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY_INPUT:-}"
fi

if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ALIBABA_CLOUD_API_KEY:-}" ] && [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "❌ 错误: 至少需要设置一个 API Key"
    exit 1
fi

echo "✅ API Keys 已设置"
echo ""

# 检查镜像
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

# 查找 Dora 主仓库路径
DORA_BINS_DIR=""
if [ -d "$HOME/dora/target/release" ]; then
    DORA_BINS_DIR="$HOME/dora/target/release"
elif [ -d "$REPO_ROOT/../../dora/target/release" ]; then
    DORA_BINS_DIR="$(cd "$REPO_ROOT/../../dora/target/release" && pwd)"
fi

if [ -z "$DORA_BINS_DIR" ]; then
    echo "⚠️  警告: 未找到 Dora Rust 二进制文件目录"
    echo "   Conference 示例需要额外的 Rust 节点："
    echo "   - dora-conference-bridge"
    echo "   - dora-conference-controller"
    echo "   - dora-maas-client"
    echo ""
    echo "   请先编译："
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
    "-e" "OPENAI_API_KEY=${OPENAI_API_KEY:-}"
    "-e" "ALIBABA_CLOUD_API_KEY=${ALIBABA_CLOUD_API_KEY:-}"
    "-e" "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}"
    "-e" "LANG=zh_CN.UTF-8"
    "-e" "LC_ALL=zh_CN.UTF-8"
    "--workdir" "/workspace"
)

# 挂载 Rust 二进制文件
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
docker run "${DOCKER_ARGS[@]}" "$IMAGE_NAME" bash -c "
    set -e

    echo \"📋 检查环境...\"
    echo \"  • Python: \$(python --version)\"
    echo \"  • Dora: \$(dora --version 2>&1 || echo '未安装')\"
    echo \"\"

    echo \"🔧 启动 dora daemon...\"
    dora up &
    DORA_PID=\$!
    sleep 3

    echo \"✅ Dora daemon 已启动 (PID: \$DORA_PID)\"
    echo \"\"

    echo \"📦 启动 dataflow: $DATAFLOW\"
    DATAFLOW_UUID=\$(dora start $DATAFLOW --detach 2>&1 | grep \"dataflow started:\" | awk '{print \$3}')
    echo \"  • Dataflow UUID: \${DATAFLOW_UUID:-<未知>}\"
    echo \"  • 等待所有节点启动...\"
    sleep 10

    echo \"\"
    echo \"📊 Dataflow 状态:\"
    dora list
    echo \"\"

    echo \"============================================\"
    echo \"✅ Dataflow 已启动！\"
    echo \"============================================\"
    echo \"\"
    echo \"接下来请在新终端中运行 TUI 界面:\"
    echo \"\"
    echo \"  cd $SCRIPT_DIR\"
    echo \"  python debate_monitor.py\"
    echo \"\"
    echo \"或者在容器内运行:\"
    echo \"\"
    echo \"  docker exec -it \$(docker ps -q -f ancestor=$IMAGE_NAME) python /workspace/debate_monitor.py\"
    echo \"\"
    echo \"提示:\"
    echo \"  • 按 Ctrl+C 停止 dataflow\"
    echo \"  • 查看日志: dora logs \$DATAFLOW_UUID\"
    echo \"\"

    trap \"echo '\\n🛑 正在停止服务...'; kill \$DORA_PID 2>/dev/null || true; exit 0\" INT TERM

    # 保持容器运行
    echo \"⏳ Dataflow 运行中，按 Ctrl+C 停止...\"
    wait \$DORA_PID
"

echo ""
echo "👋 容器已退出"
