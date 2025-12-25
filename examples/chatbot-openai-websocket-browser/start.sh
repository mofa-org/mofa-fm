#!/bin/bash
# Chatbot OpenAI WebSocket Browser 启动脚本（交互式配置）
set -Eeuo pipefail

echo "============================================"
echo "启动 Chatbot OpenAI WebSocket Browser"
echo "============================================"

to_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DORA_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEFAULT_TARGET_DIR="$DEFAULT_DORA_ROOT/target/release"
DEFAULT_CONFIG_FILE="$SCRIPT_DIR/maas_mcp_browser_config.toml"
DEFAULT_TEMPLATE_FILE="$SCRIPT_DIR/whisper-template-metal.yml"
DATAFLOW_CACHE_DIR="$SCRIPT_DIR"

read -rp "使用 Dora 根目录 [$DEFAULT_DORA_ROOT]? (Y/n) " use_default_root
use_default_root=${use_default_root:-Y}
if [[ "$(to_lower "$use_default_root")" == "n" ]]; then
  read -rp "请输入 Dora 根目录的绝对路径: " CUSTOM_DORA_ROOT
  if [[ -z "${CUSTOM_DORA_ROOT:-}" ]]; then
    echo "错误: 未提供 Dora 根目录，终止。"
    exit 1
  fi
  DORA_ROOT="$(cd "$CUSTOM_DORA_ROOT" && pwd)"
else
  DORA_ROOT="$DEFAULT_DORA_ROOT"
fi

if [[ ! -d "$DORA_ROOT" ]]; then
  echo "错误: Dora 根目录不存在: $DORA_ROOT"
  exit 1
fi

read -rp "使用 Dora 可执行文件目录 [$DEFAULT_TARGET_DIR]? (Y/n) " use_default_target
use_default_target=${use_default_target:-Y}
if [[ "$(to_lower "$use_default_target")" == "n" ]]; then
  read -rp "请输入 Dora 可执行文件目录: " CUSTOM_TARGET_DIR
  if [[ -z "${CUSTOM_TARGET_DIR:-}" ]]; then
    echo "错误: 未提供可执行文件目录，终止。"
    exit 1
  fi
  TARGET_DIR="$(cd "$CUSTOM_TARGET_DIR" && pwd)"
else
  TARGET_DIR="$DEFAULT_TARGET_DIR"
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "错误: 可执行文件目录不存在: $TARGET_DIR"
  exit 1
fi

read -rp "使用 MaaS 配置文件 [$DEFAULT_CONFIG_FILE]? (Y/n) " use_default_config
use_default_config=${use_default_config:-Y}
if [[ "$(to_lower "$use_default_config")" == "n" ]]; then
  read -rp "请输入配置文件路径: " CUSTOM_CONFIG_FILE
  if [[ -z "${CUSTOM_CONFIG_FILE:-}" ]]; then
    echo "错误: 未提供配置文件路径，终止。"
    exit 1
  fi
  CONFIG_FILE="$(cd "$(dirname "$CUSTOM_CONFIG_FILE")" && pwd)/$(basename "$CUSTOM_CONFIG_FILE")"
else
  CONFIG_FILE="$DEFAULT_CONFIG_FILE"
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "错误: 找不到 MaaS 配置文件: $CONFIG_FILE"
  exit 1
fi

read -rp "使用模板文件 [$DEFAULT_TEMPLATE_FILE]? (Y/n) " use_default_template
use_default_template=${use_default_template:-Y}
if [[ "$(to_lower "$use_default_template")" == "n" ]]; then
  read -rp "请输入模板文件路径: " CUSTOM_TEMPLATE_FILE
  if [[ -z "${CUSTOM_TEMPLATE_FILE:-}" ]]; then
    echo "错误: 未提供模板文件路径，终止。"
    exit 1
  fi
  TEMPLATE_FILE="$(cd "$(dirname "$CUSTOM_TEMPLATE_FILE")" && pwd)/$(basename "$CUSTOM_TEMPLATE_FILE")"
else
  TEMPLATE_FILE="$DEFAULT_TEMPLATE_FILE"
fi

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  echo "错误: 找不到模板文件: $TEMPLATE_FILE"
  exit 1
fi

# WebSocket 节点名称固定为 wserver
WS_NODE_NAME="wserver"

DORA_CLI="$TARGET_DIR/dora"
MAAS_BIN="$TARGET_DIR/dora-maas-client"
WS_BIN="$TARGET_DIR/dora-openai-websocket"

missing_bins=()
[[ -x "$MAAS_BIN" ]] || missing_bins+=("dora-maas-client")
[[ -x "$WS_BIN" ]] || missing_bins+=("dora-openai-websocket")

DORA_CMD=""
if [[ -x "$DORA_CLI" ]]; then
  DORA_CMD="$DORA_CLI"
else
  DORA_CMD="$(command -v dora || true)"
  if [[ -n "$DORA_CMD" ]]; then
    echo "提示: 使用系统中的 dora CLI: $DORA_CMD"
  else
    missing_bins+=("dora")
  fi
fi

if (( ${#missing_bins[@]} > 0 )); then
  echo "警告: 未找到以下可执行文件: ${missing_bins[*]}"
  read -rp "是否在 $DORA_ROOT 中执行 'cargo build --release'? (Y/n) " build_choice
  build_choice=${build_choice:-Y}
  if [[ "$(to_lower "$build_choice")" == "y" ]]; then
    pushd "$DORA_ROOT" >/dev/null
    cargo build --release
    popd >/dev/null
  else
    echo "错误: 缺少必需的可执行文件，终止。"
    exit 1
  fi
  if [[ -z "$DORA_CMD" ]]; then
    if [[ -x "$DORA_CLI" ]]; then
      DORA_CMD="$DORA_CLI"
    else
      DORA_CMD="$(command -v dora || true)"
    fi
  fi
  if [[ -z "$DORA_CMD" ]]; then
    echo "错误: 构建后仍未找到 dora CLI。"
    exit 1
  fi
fi

PATH="$TARGET_DIR:$PATH"
export PATH

DORA_RUNNING=0
if "$DORA_CMD" check >/dev/null 2>&1; then
  DORA_RUNNING=1
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  read -rsp "请输入 OPENAI_API_KEY: " OPENAI_API_KEY
  echo ""
fi

if [[ -z "${OPENAI_API_KEY}" ]]; then
  echo "错误: OPENAI_API_KEY 不能为空，终止。"
  exit 1
fi

echo "已设置 OPENAI_API_KEY（长度: ${#OPENAI_API_KEY}）"

export OPENAI_API_KEY
export MAAS_CONFIG_PATH="$CONFIG_FILE"
export SPAWN_MAAS=0

PRIMESPEECH_DIR="${PRIMESPEECH_MODEL_DIR:-$HOME/.dora/models/primespeech}"
ASR_DIR="$HOME/.dora/models/asr"

missing_models=0

if [[ ! -d "$PRIMESPEECH_DIR" ]] || [[ -z "$(ls -A "$PRIMESPEECH_DIR" 2>/dev/null)" ]]; then
  echo "警告: 未检测到 PrimeSpeech 模型目录: $PRIMESPEECH_DIR"
  echo "   下载命令: python \"$DORA_ROOT/examples/model-manager/download_models.py\" --download primespeech"
  missing_models=1
fi

if [[ ! -d "$ASR_DIR" ]] || [[ -z "$(ls -A "$ASR_DIR" 2>/dev/null)" ]]; then
  echo "警告: 未检测到 FunASR 模型目录: $ASR_DIR"
  echo "   下载命令: python \"$DORA_ROOT/examples/model-manager/download_models.py\" --download funasr"
  missing_models=1
fi

if (( missing_models )); then
  read -rp "仍要继续启动吗？(y/N) " continue_without_models
  continue_without_models=${continue_without_models:-N}
  if [[ "$(to_lower "$continue_without_models")" != "y" ]]; then
    echo "提示: 已取消启动。"
    exit 0
  fi
fi

echo ""
echo "当前配置："
echo "  • 脚本目录:          $SCRIPT_DIR"
echo "  • Dora 根目录:       $DORA_ROOT"
echo "  • 可执行文件目录:    $TARGET_DIR"
echo "  • MaaS 配置:         $CONFIG_FILE"
echo "  • 模板文件:          $TEMPLATE_FILE"
echo "  • 节点名称:          $WS_NODE_NAME"
echo "  • Host Dataflow:     $SCRIPT_DIR/host-dataflow.yml"
echo ""
read -rp "确认以上信息无误后继续？(Y/n) " confirm_all
confirm_all=${confirm_all:-Y}
if [[ "$(to_lower "$confirm_all")" == "n" ]]; then
  echo "提示: 已取消启动。"
  exit 0
fi

STARTED_DORA=0
if (( DORA_RUNNING )); then
  read -rp "检测到 dora daemon 已在运行，是否复用当前实例？(Y/n) " reuse_dora
  reuse_dora=${reuse_dora:-Y}
  if [[ "$(to_lower "$reuse_dora")" == "y" ]]; then
    echo "复用现有 dora daemon。"
    DORA_UP_PID=""
  else
    DORA_RUNNING=0
  fi
fi

if (( ! DORA_RUNNING )); then
  echo "清理所有旧进程..."
  pkill -9 -f "dora coordinator" 2>/dev/null || true
  pkill -9 -f "dora start" 2>/dev/null || true
  pkill -9 -f "dora up" 2>/dev/null || true
  pkill -9 -f "dora-openai-websocket" 2>/dev/null || true
  pkill -9 -f "dora-maas-client" 2>/dev/null || true
  echo "   等待进程完全退出..."
  sleep 4

  echo "启动 dora daemon..."
  pushd "$DORA_ROOT" >/dev/null
  "$DORA_CMD" up &
  DORA_UP_PID=$!
  STARTED_DORA=1
  sleep 5
  if ! kill -0 "$DORA_UP_PID" 2>/dev/null; then
    echo "错误: dora daemon 启动失败，请检查终端输出或运行 'dora up' 手动排查。"
    exit 1
  fi
  popd >/dev/null
else
  DORA_UP_PID=""
fi

echo "启动 Host Dataflow..."
HOST_DATAFLOW="$SCRIPT_DIR/host-dataflow.yml"
if [[ ! -f "$HOST_DATAFLOW" ]]; then
  echo "创建 host-dataflow.yml..."
  cat > "$HOST_DATAFLOW" << 'HOSTEOF'
# Host dataflow for WebSocket server
# The wserver node will be added dynamically via --name argument
nodes:
  - id: wserver
    path: dynamic
    outputs:
      - dummy
HOSTEOF
fi

DATAFLOW_UUID=$("$DORA_CMD" start "$HOST_DATAFLOW" --detach 2>&1 | grep "dataflow started:" | awk '{print $3}')
echo "   Host Dataflow UUID: ${DATAFLOW_UUID:-<未知>}"
echo "   等待 dataflow 启动..."
sleep 3

echo "启动 WebSocket 服务器..."
pushd "$SCRIPT_DIR" >/dev/null
echo "   监听地址: 0.0.0.0:8123"
echo "   模板目录: $DATAFLOW_CACHE_DIR"
echo "   连接节点: $WS_NODE_NAME"
echo ""
cleanup() {
  echo "捕获到退出信号，正在清理..."
  if [[ -n "${DATAFLOW_UUID:-}" ]]; then
    echo "停止 dataflow: $DATAFLOW_UUID"
    "$DORA_CMD" stop "$DATAFLOW_UUID" 2>/dev/null || true
  fi
  if [[ -n "${DORA_UP_PID:-}" ]]; then
    kill "$DORA_UP_PID" 2>/dev/null || true
    wait "$DORA_UP_PID" 2>/dev/null || true
  fi
}
trap cleanup INT TERM

SPAWN_MAAS=0 "$WS_BIN" --name "$WS_NODE_NAME"

# Cleanup on exit
if [[ -n "${DATAFLOW_UUID:-}" ]]; then
  "$DORA_CMD" stop "$DATAFLOW_UUID" 2>/dev/null || true
fi
if [[ -n "${DORA_UP_PID:-}" ]]; then
  kill "$DORA_UP_PID" 2>/dev/null || true
  wait "$DORA_UP_PID" 2>/dev/null || true
fi
popd >/dev/null
