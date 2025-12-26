#!/bin/bash
# 顶层示例启动器：提供简洁 TUI 选择各示例 start.sh
set -Eeo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LABELS=(
  "Chatbot OpenAI"
  "Chatbot Alicloud"
  "Chatbot OpenAI WebSocket Browser"
  "Conference"
)
PATHS=(
  "examples/chatbot-openai-0905/start.sh"
  "examples/chatbot-alicloud-0908/start.sh"
  "examples/chatbot-openai-websocket-browser/start.sh"
  "examples/conference/start.sh"
)

color() {
  local code="$1"
  shift
  printf "\033[%sm%s\033[0m" "$code" "$*"
}

draw_frame() {
  local border
  border=$(printf '─%.0s' {1..60})
  echo "┌${border}┐"
  printf "│%-60s│\n" "$(color '1;36' ' MOFA Dora Examples Launcher ')"
  echo "├${border}┤"
  local idx=0
  local total=${#LABELS[@]}
  while (( idx < total )); do
    local key=$((idx + 1))
    local label="${LABELS[$idx]}"
    printf "│  %s %-3s %s%-50s%s │\n" \
      "$(color '1;34' '[')" \
      "$key" \
      "$(color '1;34' ']')" \
      "$(color '1;37' "$label")" \
      ""
    ((idx++))
  done
  echo "├${border}┤"
  printf "│ %-58s │\n" "输入 1-${#LABELS[@]} 选择示例，或输入 q 退出"
  echo "└${border}┘"
}

launch_example() {
  local index="$1"
  if (( index < 0 || index >= ${#PATHS[@]} )); then
    echo "错误: 无效的示例索引 $index" >&2
    exit 1
  fi
  local rel_path="${PATHS[$index]}"
  local abs_path="$SCRIPT_DIR/$rel_path"
  local label="${LABELS[$index]}"
  if [[ ! -f "$abs_path" ]]; then
    echo "错误: 找不到启动脚本 $rel_path" >&2
    exit 1
  fi
  if [[ ! -x "$abs_path" ]]; then
    chmod +x "$abs_path"
  fi
  echo ""
  echo "$(color '1;32' "▶ 正在启动：$label")"
  echo "（脚本路径：$rel_path）"
  echo ""
  exec "$abs_path"
}

clear
draw_frame
read -rp "> " choice

case "$choice" in
  q|Q)
    echo "已退出。"
    exit 0
    ;;
  ''|*[!0-9]*)
    echo "无效选择：$choice" >&2
    exit 1
    ;;
  *)
    index=$((choice - 1))
    if (( index < 0 || index >= ${#LABELS[@]} )); then
      echo "无效选择：$choice" >&2
      exit 1
    fi
    launch_example "$index"
    ;;
esac
