# Chatbot Alicloud 0908 使用指南

## 快速启动

### 方法一：使用启动脚本（推荐）

```bash
cd /Users/yao/Desktop/code/local-dev/mofa-fm-simple/dora/examples/chatbot-alicloud-0908
./start.sh
```

脚本会依次确认 Dora 根目录、可执行文件目录、MaaS 配置文件，并提示输入 `ALIBABA_CLOUD_API_KEY`（必填）和可选的 `OPENAI_API_KEY`。同时检查 PrimeSpeech/FunASR 模型是否已下载。

### 方法二：手动启动

```bash
# 1. 进入项目目录
cd /Users/yao/Desktop/code/local-dev/mofa-fm-simple/dora/examples/chatbot-alicloud-0908

# 2. 设置环境变量
export ALIBABA_CLOUD_API_KEY="<your-alibaba-key>"
export OPENAI_API_KEY="<optional-openai-key>"
export SPAWN_MAAS=0
export MAAS_CONFIG_PATH="$PWD/maas_mcp_browser_config.toml"

# 3. 启动 dora daemon
cd ../../
dora up &
sleep 3

# 4. 启动 dataflow
cd examples/chatbot-alicloud-0908
dora start chatbot-staticflow.yml &
sleep 10

# 5. 启动 WebSocket 服务器
SPAWN_MAAS=0 ../../target/release/dora-openai-websocket --name wserver
```

## 测试连接

启动成功后，在另一个终端运行：

```bash
cd /Users/yao/Desktop/code/local-dev/mofa-fm-simple/dora/examples/chatbot-alicloud-0908
/opt/homebrew/opt/python@3.11/bin/python3.11 test_ws.py
```

脚本会连接 `ws://localhost:8123`，发送 `session.update` 与 `response.create`，并打印返回的 `audio.delta` 和 `text.delta`。

## 系统架构

```
WebSocket 客户端 (ws://localhost:8123)
    ↓
WebSocket 服务器 (wserver - 动态节点)
    ↓
Dataflow 静态节点：
    ├── speech-monitor (语音检测)
    ├── asr (语音识别)
    ├── maas-client (阿里云 MaaS) ← 静态节点
    ├── text-segmenter (文本分段)
    └── primespeech (TTS 合成)
```

## 环境变量说明

- `ALIBABA_CLOUD_API_KEY`: 阿里云 MaaS API 密钥（必需）
- `OPENAI_API_KEY`: 可选，用于配置中包含的 OpenAI 模型
- `SPAWN_MAAS=0`: 禁用动态 maas-client spawn（必需）
- `MAAS_CONFIG_PATH`: 指定 `maas_mcp_browser_config.toml` 的路径

## 常用命令

```bash
# 查看运行中的 dataflow
dora list

# 查看节点日志
dora logs <UUID> <node-name>
# 例如：dora logs 019b5074-6d34-74b4-a38a-004501e570c4 maas-client

# 停止 dataflow
dora stop <UUID>

# 停止所有服务
pkill -9 dora
pkill -f dora-openai-websocket
```

## 故障排查

### WebSocket 连接失败
```bash
lsof -i:8123
lsof -ti:8123 | xargs kill -9
```

### Dataflow 启动失败
```bash
dora logs <UUID>
python3 -c "import torch; print(torch.__version__)"
```

### API 调用失败
```bash
echo "$ALIBABA_CLOUD_API_KEY"
```

## 日志位置

- Dataflow 日志: `out/<dataflow-uuid>/log_<node-name>.txt`
- WebSocket 服务器: 控制台输出

## 性能提示

- 首次运行会加载 ASR/TTS 模型，需要等待数十秒
- 确保网络通畅以调用阿里云 MaaS
- 可通过修改 `maas_mcp_browser_config.toml` 切换阿里云模型（如 `qwen-max`、`deepseek-v3` 等）
