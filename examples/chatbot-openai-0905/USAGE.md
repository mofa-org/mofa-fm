# Chatbot OpenAI 0905 使用指南

## 快速启动

### 方法一：使用启动脚本（推荐）

```bash
cd /Users/yao/Desktop/code/local-dev/mofa-fm-simple/dora/examples/chatbot-openai-0905
./start.sh
```

### 方法二：手动启动

```bash
# 1. 进入项目目录
cd /Users/yao/Desktop/code/local-dev/mofa-fm-simple/dora/examples/chatbot-openai-0905

# 2. 设置环境变量
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY_HERE"
export SPAWN_MAAS=0

# 3. 启动 dora daemon
cd ../../
dora up &
sleep 3

# 4. 启动 dataflow
cd examples/chatbot-openai-0905
OPENAI_API_KEY="$OPENAI_API_KEY" dora start chatbot-staticflow.yml &
sleep 10

# 5. 启动 WebSocket 服务器
SPAWN_MAAS=0 ../../target/release/dora-openai-websocket --name wserver
```

## 测试连接

启动成功后，在另一个终端运行：

```bash
cd /Users/yao/Desktop/code/local-dev/mofa-fm-simple/dora/examples/chatbot-openai-0905
python3 test_websocket.py
```

## 系统架构

```
WebSocket 客户端 (ws://localhost:8123)
    ↓
WebSocket 服务器 (wserver - 动态节点)
    ↓
Dataflow 静态节点：
    ├── speech-monitor (语音检测)
    ├── asr (语音识别)
    ├── maas-client (LLM 处理) ← 静态节点！
    ├── text-segmenter (文本分段)
    └── primespeech (TTS 合成)
```

## 重要说明

### 已修复的问题

**maas-client spawn 冲突**
- 之前：WebSocket 服务器尝试动态 spawn maas-client，但它已作为静态节点运行
- 现在：设置 `SPAWN_MAAS=0` 禁用动态 spawn，使用静态节点

### 环境变量说明

- `OPENAI_API_KEY`: OpenAI API 密钥（必需）
- `SPAWN_MAAS=0`: 禁用动态 maas-client spawn（必需）

## 常用命令

```bash
# 查看运行中的 dataflow
dora list

# 查看节点日志
dora logs <UUID> <node-name>
# 例如：dora logs 019b4c41-3037-769a-9142-9c2b9ee98566 maas-client

# 停止 dataflow
dora stop <UUID>

# 停止所有服务
pkill -9 dora
pkill -f dora-openai-websocket
```

## 故障排查

### WebSocket 连接失败
```bash
# 检查端口是否被占用
lsof -i:8123

# 如果被占用，杀掉进程
lsof -ti:8123 | xargs kill -9
```

### Dataflow 启动失败
```bash
# 查看详细错误
dora logs <UUID>

# 检查 PyTorch 是否安装
python3 -c "import torch; print(torch.__version__)"
```

### API 调用失败
```bash
# 验证 API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | head
```

## 日志位置

- Dataflow 日志: `out/<dataflow-uuid>/log_<node-name>.txt`
- WebSocket 服务器: 控制台输出

## 性能提示

- 首次运行会下载 ASR/TTS 模型，需要一些时间
- 建议在稳定网络环境下运行
- GPU 可用时会自动加速 ASR
