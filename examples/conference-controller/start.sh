#!/bin/bash
# Conference Controller 启动脚本
set -Eeuo pipefail

echo "============================================"
echo "启动 Conference Controller Example"
echo "============================================"

to_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DORA_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEFAULT_TARGET_DIR="$DEFAULT_DORA_ROOT/target/release"

# 列出可用的 dataflow 文件
echo "可用的 dataflow 文件："
echo "  1. dataflow-complete.yml (完整配置)"
echo "  2. priority-interview.yml (优先级策略 - 面试)"
echo "  3. ratio-debate.yml (比率策略 - 辩论)"
echo "  4. sequential-simple.yml (顺序策略 - 简单)"
echo ""
read -rp "选择 dataflow (1-4) [1]: " dataflow_choice
dataflow_choice=${dataflow_choice:-1}

case $dataflow_choice in
  1) DATAFLOW_FILE="$SCRIPT_DIR/dataflow-complete.yml" ;;
  2) DATAFLOW_FILE="$SCRIPT_DIR/priority-interview.yml" ;;
  3) DATAFLOW_FILE="$SCRIPT_DIR/ratio-debate.yml" ;;
  4) DATAFLOW_FILE="$SCRIPT_DIR/sequential-simple.yml" ;;
  *) echo "无效选择，使用默认: dataflow-complete.yml"
     DATAFLOW_FILE="$SCRIPT_DIR/dataflow-complete.yml" ;;
esac

echo "已选择: $(basename "$DATAFLOW_FILE")"

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

DORA_CLI="$TARGET_DIR/dora"
MAAS_BIN="$TARGET_DIR/dora-maas-client"
BRIDGE_BIN="$TARGET_DIR/dora-conference-bridge"
CONTROLLER_BIN="$TARGET_DIR/dora-conference-controller"
TERMINAL_PRINT_BIN="$TARGET_DIR/terminal-print"

missing_bins=()
[[ -x "$MAAS_BIN" ]] || missing_bins+=("dora-maas-client")
[[ -x "$BRIDGE_BIN" ]] || missing_bins+=("dora-conference-bridge")
[[ -x "$CONTROLLER_BIN" ]] || missing_bins+=("dora-conference-controller")
[[ -x "$TERMINAL_PRINT_BIN" ]] || missing_bins+=("terminal-print")

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

if [[ ! -f "$DATAFLOW_FILE" ]]; then
  echo "错误: 找不到 dataflow 文件: $DATAFLOW_FILE"
  exit 1
fi

# 检查 API keys
if [[ -z "${OPENAI_API_KEY:-}" && -z "${ALIBABA_CLOUD_API_KEY:-}" && -z "${DEEPSEEK_API_KEY:-}" ]]; then
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

if [[ -z "${OPENAI_API_KEY:-}" && -z "${ALIBABA_CLOUD_API_KEY:-}" && -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "错误: 至少需要设置一个 API Key"
  exit 1
fi

echo "已设置 API Keys"
[[ -n "${OPENAI_API_KEY:-}" ]] && echo "  • OPENAI_API_KEY (长度: ${#OPENAI_API_KEY})"
[[ -n "${ALIBABA_CLOUD_API_KEY:-}" ]] && echo "  • ALIBABA_CLOUD_API_KEY (长度: ${#ALIBABA_CLOUD_API_KEY})"
[[ -n "${DEEPSEEK_API_KEY:-}" ]] && echo "  • DEEPSEEK_API_KEY (长度: ${#DEEPSEEK_API_KEY})"

export OPENAI_API_KEY
export ALIBABA_CLOUD_API_KEY
export DEEPSEEK_API_KEY

echo ""
echo "当前配置："
echo "  • 脚本目录:          $SCRIPT_DIR"
echo "  • Dora 根目录:       $DORA_ROOT"
echo "  • 可执行文件目录:    $TARGET_DIR"
echo "  • Dataflow 文件:     $DATAFLOW_FILE"
echo ""
read -rp "确认以上信息无误后继续？(Y/n) " confirm_all
confirm_all=${confirm_all:-Y}
if [[ "$(to_lower "$confirm_all")" == "n" ]]; then
  echo "提示: 已取消启动。"
  exit 0
fi

echo "清理所有旧进程..."
pkill -9 -f "dora coordinator" 2>/dev/null || true
pkill -9 -f "dora start" 2>/dev/null || true
pkill -9 -f "dora up" 2>/dev/null || true
pkill -9 -f "dora-maas-client" 2>/dev/null || true
pkill -9 -f "dora-conference-bridge" 2>/dev/null || true
pkill -9 -f "dora-conference-controller" 2>/dev/null || true
pkill -9 -f "terminal-print" 2>/dev/null || true
echo "   等待进程完全退出..."
sleep 4

echo "启动 dora daemon..."
pushd "$DORA_ROOT" >/dev/null
"$DORA_CMD" up &
DORA_UP_PID=$!
sleep 5
popd >/dev/null

echo "启动 dataflow..."
DATAFLOW_UUID=$("$DORA_CMD" start "$DATAFLOW_FILE" --detach 2>&1 | grep "dataflow started:" | awk '{print $3}')
echo "   Dataflow UUID: ${DATAFLOW_UUID:-<未知>}"
echo "   等待所有节点启动..."
sleep 10

echo "检查 dataflow 状态..."
"$DORA_CMD" list | grep -E "UUID|Running"

echo ""
echo "============================================"
echo "Conference Controller 启动完成！"
echo "============================================"
echo ""
echo "提示："
echo "  - 查看终端输出观察 LLM 交互"
echo "  - 查看详细日志: dora logs $DATAFLOW_UUID"
echo "  - 停止dataflow: dora stop $DATAFLOW_UUID"
echo "  - 按 Ctrl+C 停止 daemon"
echo ""

trap 'echo "捕获到退出信号，正在清理..."; kill "$DORA_UP_PID" 2>/dev/null || true' INT TERM

echo "按 Ctrl+C 停止 dataflow daemon..."
wait "$DORA_UP_PID"
