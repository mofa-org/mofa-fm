#!/bin/bash
# Conference 示例统一启动脚本
set -Eeuo pipefail

echo "============================================"
echo "启动 Conference 示例"
echo "============================================"

to_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEFAULT_TARGET_DIR="$PROJECT_ROOT/target/release"
if [[ ! -d "$DEFAULT_TARGET_DIR" ]]; then
  ALT_TARGET_DIR="$PROJECT_ROOT/../dora/target/release"
  if [[ -d "$ALT_TARGET_DIR" ]]; then
    DEFAULT_TARGET_DIR="$(cd "$ALT_TARGET_DIR" && pwd)"
  fi
fi
CONTROL_HOST="127.0.0.1"
CONTROL_PORT="${DORA_CONTROL_PORT:-16012}"
COORDINATOR_PORT="${DORA_COORD_PORT:-16329}"

DATAFLOW_CHOICES=(
  "dataflow-debate-sequential.yml|辩论：顺序策略"
  "dataflow-study-sequential.yml|学习：顺序策略"
  "dataflow-study-audio.yml|学习：音频模式"
  "dataflow-study-audio-multi.yml|学习：多麦克风"
  "dataflow-study-audio-kokoro.yml|学习：Kokoro TTS"
)

echo "可用的数据流："
index=1
for item in "${DATAFLOW_CHOICES[@]}"; do
  file="${item%%|*}"
  label="${item#*|}"
  printf "  %d. %s (%s)\n" "$index" "$label" "$file"
  ((index++))
done

read -rp "请选择要启动的序号 [1]: " selection
selection=${selection:-1}

if ! [[ "$selection" =~ ^[1-9][0-9]*$ ]] || (( selection < 1 || selection > ${#DATAFLOW_CHOICES[@]} )); then
  echo "无效选择，使用默认配置（1）"
  selection=1
fi

choice="${DATAFLOW_CHOICES[$((selection-1))]}"
DATAFLOW_FILE="$SCRIPT_DIR/${choice%%|*}"
DATAFLOW_LABEL="${choice#*|}"

if [[ ! -f "$DATAFLOW_FILE" ]]; then
  echo "错误: 找不到 dataflow 文件: $DATAFLOW_FILE"
  exit 1
fi

read -rp "使用默认的 Dora 可执行文件目录 [$DEFAULT_TARGET_DIR]? (Y/n) " use_default_target
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

# 确保 dataflow 中引用的 ../../target/release 指向实际二进制目录
EXPECTED_RELEASE_DIR="$PROJECT_ROOT/target/release"
if [[ ! -e "$EXPECTED_RELEASE_DIR" ]]; then
  mkdir -p "$(dirname "$EXPECTED_RELEASE_DIR")"
  ln -s "$TARGET_DIR" "$EXPECTED_RELEASE_DIR"
elif [[ -L "$EXPECTED_RELEASE_DIR" ]]; then
  CURRENT_LINK="$(readlink "$EXPECTED_RELEASE_DIR")"
  if [[ "$CURRENT_LINK" != "$TARGET_DIR" ]]; then
    rm "$EXPECTED_RELEASE_DIR"
    ln -s "$TARGET_DIR" "$EXPECTED_RELEASE_DIR"
  fi
fi

DORA_CLI="$TARGET_DIR/dora"
MAAS_BIN="$TARGET_DIR/dora-maas-client"
BRIDGE_BIN="$TARGET_DIR/dora-conference-bridge"
CONTROLLER_BIN="$TARGET_DIR/dora-conference-controller"

missing_bins=()
[[ -x "$MAAS_BIN" ]] || missing_bins+=("dora-maas-client")
[[ -x "$BRIDGE_BIN" ]] || missing_bins+=("dora-conference-bridge")
[[ -x "$CONTROLLER_BIN" ]] || missing_bins+=("dora-conference-controller")

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
  echo "缺少以下可执行文件: ${missing_bins[*]}"
  read -rp "是否在 $PROJECT_ROOT 中执行 'cargo build --release'? (Y/n) " build_choice
  build_choice=${build_choice:-Y}
  if [[ "$(to_lower "$build_choice")" == "y" ]]; then
    pushd "$PROJECT_ROOT" >/dev/null
    cargo build --release
    popd >/dev/null
    DORA_CMD="${DORA_CMD:-$TARGET_DIR/dora}"
    if [[ ! -x "$DORA_CMD" ]]; then
      echo "错误: 构建后仍未找到 dora CLI。"
      exit 1
    fi
  else
    echo "错误: 缺少必需的可执行文件，终止。"
    exit 1
  fi
fi

PATH="$TARGET_DIR:$PATH"
export PATH

if [[ -z "${OPENAI_API_KEY:-}" && -z "${ALIBABA_CLOUD_API_KEY:-}" && -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "请输入至少一个 API Key（其他可留空）："
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
  echo "错误: 至少需要设置一个 API Key。"
  exit 1
fi

export OPENAI_API_KEY
export ALIBABA_CLOUD_API_KEY
export DEEPSEEK_API_KEY

echo ""
echo "启动配置："
echo "  数据流:            $DATAFLOW_LABEL"
echo "  Dataflow 文件:     $DATAFLOW_FILE"
echo "  可执行文件目录:    $TARGET_DIR"
echo ""

cleanup() {
  if [[ -n "${DATAFLOW_UUID:-}" ]]; then
    "$DORA_CMD" stop "$DATAFLOW_UUID" --coordinator-addr "$CONTROL_HOST" --coordinator-port "$CONTROL_PORT" >/dev/null 2>&1 || true
  fi
  if [[ -n "${DAEMON_PID:-}" ]]; then
    if ! kill "$DAEMON_PID" >/dev/null 2>&1; then
      sudo kill "$DAEMON_PID" >/dev/null 2>&1 || true
    fi
    wait "$DAEMON_PID" 2>/dev/null || true
  fi
  if [[ -n "${COORDINATOR_PID:-}" ]]; then
    if ! kill "$COORDINATOR_PID" >/dev/null 2>&1; then
      sudo kill "$COORDINATOR_PID" >/dev/null 2>&1 || true
    fi
    wait "$COORDINATOR_PID" 2>/dev/null || true
  fi
  [[ -n "${COORD_LOG:-}" ]] && rm -f "$COORD_LOG"
  [[ -n "${DAEMON_LOG:-}" ]] && rm -f "$DAEMON_LOG"
}
trap cleanup EXIT INT TERM

echo "清理旧进程..."
pkill -9 -f "dora coordinator" 2>/dev/null || true
pkill -9 -f "dora up" 2>/dev/null || true
pkill -9 -f "dora start" 2>/dev/null || true
pkill -9 -f "dora-maas-client" 2>/dev/null || true
pkill -9 -f "dora-conference-bridge" 2>/dev/null || true
pkill -9 -f "dora-conference-controller" 2>/dev/null || true
sleep 3

echo "启动 dora coordinator (control端口: $CONTROL_PORT, daemon端口: $COORDINATOR_PORT)..."
pushd "$PROJECT_ROOT" >/dev/null
COORD_LOG="$(mktemp /tmp/dora-coordinator.XXXXXX.log)"
"$DORA_CMD" coordinator \
  --quiet \
  --interface "$CONTROL_HOST" \
  --control-interface "$CONTROL_HOST" \
  --port "$COORDINATOR_PORT" \
  --control-port "$CONTROL_PORT" \
  >"$COORD_LOG" 2>&1 &
COORDINATOR_PID=$!
sleep 3
if ! kill -0 "$COORDINATOR_PID" 2>/dev/null; then
  if grep -q "Operation not permitted" "$COORD_LOG"; then
    echo "dora coordinator 需要管理员权限，尝试使用 sudo 启动..."
    sudo -E "$DORA_CMD" coordinator \
      --quiet \
      --interface "$CONTROL_HOST" \
      --control-interface "$CONTROL_HOST" \
      --port "$COORDINATOR_PORT" \
      --control-port "$CONTROL_PORT" \
      >"$COORD_LOG" 2>&1 &
    COORDINATOR_PID=$!
    sleep 3
  fi
fi
if ! kill -0 "$COORDINATOR_PID" 2>/dev/null; then
  echo "dora coordinator 启动失败："
  cat "$COORD_LOG"
  exit 1
fi

echo "启动 dora daemon..."
DAEMON_LOG="$(mktemp /tmp/dora-daemon.XXXXXX.log)"
"$DORA_CMD" daemon \
  --quiet \
  --coordinator-addr "$CONTROL_HOST" \
  --coordinator-port "$COORDINATOR_PORT" \
  >"$DAEMON_LOG" 2>&1 &
DAEMON_PID=$!
sleep 3
if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
  if grep -q "Permission denied" "$DAEMON_LOG"; then
    echo "dora daemon 启动需要管理员权限，尝试使用 sudo..."
    sudo -E "$DORA_CMD" daemon \
      --quiet \
      --coordinator-addr "$CONTROL_HOST" \
      --coordinator-port "$COORDINATOR_PORT" \
      >"$DAEMON_LOG" 2>&1 &
    DAEMON_PID=$!
    sleep 3
  fi
fi
if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
  echo "dora daemon 启动失败："
  cat "$DAEMON_LOG"
  exit 1
fi
popd >/dev/null

echo "启动 dataflow..."
start_output="$("$DORA_CMD" start "$DATAFLOW_FILE" --detach --coordinator-addr "$CONTROL_HOST" --coordinator-port "$CONTROL_PORT" 2>&1 || true)"
echo "$start_output"
DATAFLOW_UUID="$(printf '%s\n' "$start_output" | grep -Eo 'dataflow started: ([0-9a-f-]+)' | awk '{print $3}' || true)"
sleep 8

echo "当前 dataflow 列表："
"$DORA_CMD" list --coordinator-port "$CONTROL_PORT" || true

choose_python() {
  local candidate
  for candidate in \
    "${PYTHON_BIN:-}" \
    "$(command -v python3.11 2>/dev/null)" \
    "$(command -v python3 2>/dev/null)" \
    "/opt/homebrew/bin/python3" \
    "$(command -v python 2>/dev/null)"; do
    if [[ -x "$candidate" ]]; then
      if "$candidate" -c "import pyarrow" >/dev/null 2>&1; then
        echo "$candidate"
        return
      fi
    fi
  done
  echo ""
}

PYTHON_BIN="$(choose_python)"
if [[ -z "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3 || command -v python || true)"
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "提示: 未找到可用的 Python 解释器，无法自动启动 debate_monitor.py。"
else
  echo ""
  read -rp "是否立即运行 debate_monitor.py？(Y/n) " run_monitor
  run_monitor=${run_monitor:-Y}
  if [[ "$(to_lower "$run_monitor")" != "n" ]]; then
    if ! "$PYTHON_BIN" -c "import pyarrow" >/dev/null 2>&1; then
      echo "提示: 当前 Python 解释器缺少 pyarrow，请先运行 'pip install pyarrow rich' 或手动指定解释器后重试。"
    else
      echo "已启动 debate_monitor.py，退出后脚本将自动清理 dataflow。"
      pushd "$SCRIPT_DIR" >/dev/null
      "$PYTHON_BIN" debate_monitor.py || true
      popd >/dev/null
    fi
  else
    echo "可随时手动执行：python debate_monitor.py"
  fi
fi
    echo "已启动 debate_monitor.py，退出后脚本将自动清理 dataflow。"
    pushd "$SCRIPT_DIR" >/dev/null
    "$PYTHON_BIN" debate_monitor.py || true
    popd >/dev/null
  else
    echo "可随时手动执行：python debate_monitor.py"
  fi
fi

echo ""
echo "运行结束，正在清理..."
