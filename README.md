
## 仓库结构

```
.
├── examples/           
│   ├── chatbot-alicloud-0908/      # Alicloud 聊天机器人
│   ├── chatbot-openai-0905/        # OpenAI 聊天机器人
│   ├── chatbot-openai-websocket-browser/  # WebSocket 浏览器聊天机器人
│   ├── conference/                 # 会议/辩论示例
│   └── conference-controller/      # 会议控制器示例
└── node-hub/           
    ├── dora-asr/                   # 语音识别
    ├── dora-kokoro-tts/            # Kokoro TTS
    ├── dora-primespeech/           # PrimeSpeech TTS
    ├── dora-speechmonitor/         # 语音监控
    └── dora-text-segmenter/        # 文本分段
```

## 🐳 Docker 快速开始（推荐）

**零配置，一键启动！** 无需安装 Rust、Python 等依赖。

### 前置条件

- Docker Desktop 或 Docker Engine
- 至少一个 API Key (OPENAI/ALIBABA_CLOUD/DEEPSEEK)

### 使用步骤

```bash
# 1. 克隆仓库
git clone -b pure-dataflow https://github.com/mofa-org/mofa-fm.git
cd mofa-fm

# 2. 构建 Docker 镜像（仅首次，约 10-20 分钟）
./build-docker.sh

# 3. 运行任意示例
cd examples/chatbot-openai-0905
export OPENAI_API_KEY="your-key-here"
./docker-start.sh
```

**✨ 优势**：
- ✅ 无需配置环境
- ✅ 支持中文显示
- ✅ 自动 GPU 加速（如果可用）
- ✅ 环境完全隔离

**📖 详细文档**: 查看 [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)

---

## 🔧 本地开发模式

如果需要修改代码或深度开发，可以使用本地安装方式：

### 前置条件

1. **Rust 环境**：需要安装 Rust 和 Cargo
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Python 环境**：Python 3.12+
   ```bash
   # 建议使用 conda 或 venv
   conda create -n dora python=3.12
   conda activate dora
   ```

3. **Dora 框架**：需要完整的 Dora 仓库以编译 Rust 节点
   ```bash
   git clone https://github.com/dora-rs/dora.git
   cd dora
   cargo build --release
   ```

4. **API Keys**：至少需要以下之一
   - `OPENAI_API_KEY`
   - `ALIBABA_CLOUD_API_KEY`
   - `DEEPSEEK_API_KEY`

### 编译 Rust 节点

这些示例依赖以下 Rust 节点，需要在 Dora 主仓库中编译：

```bash
cd /path/to/dora
cargo build --release -p dora-maas-client
cargo build --release -p dora-conference-bridge
cargo build --release -p dora-conference-controller
cargo build --release -p dora-openai-websocket  # 或 dora-text-websocket
cargo build --release -p terminal-print
```

编译完成后，这些可执行文件会在 `target/release/` 目录下。

### 安装 Python 依赖

```bash
# 安装 node-hub 节点
cd node-hub/dora-asr
pip install -e .

cd ../dora-primespeech
pip install -e .

cd ../dora-kokoro-tts
pip install -e .

cd ../dora-speechmonitor
pip install -e .

cd ../dora-text-segmenter
pip install -e .
```

## 启动脚本

每个示例都提供了便捷的启动脚本：

- **chatbot-openai-0905**: `./start.sh` - 自动配置并启动 OpenAI 聊天机器人
- **chatbot-alicloud-0908**: `./start.sh` - 自动配置并启动阿里云聊天机器人
- **chatbot-openai-websocket-browser**: `./start.sh` - 启动 WebSocket 聊天机器人
- **conference**: `./start-debate.sh` - 启动辩论系统（需配合 `debate_monitor.py` 使用）
- **conference**: `./launch_group_study.sh` - 启动群体学习系统（手动启动指南）
- **conference-controller**: `./start.sh` - 交互式选择控制策略并启动

所有启动脚本都支持交互式配置，会自动检查依赖、设置路径、验证环境变量等。

## 示例说明

### 1. Chatbot OpenAI (chatbot-openai-0905)

基于 OpenAI API 的语音聊天机器人。

**特性**：
- 实时语音识别（FunASR）
- OpenAI GPT 对话
- PrimeSpeech TTS 语音合成
- WebSocket 接口

**启动**：
```bash
cd examples/chatbot-openai-0905
export OPENAI_API_KEY="your-key-here"
./start.sh
```

然后在浏览器中打开 WebSocket 客户端连接 `ws://localhost:8123`

**配置文件**：
- `chatbot-staticflow.yml` - 主 dataflow
- `maas_mcp_browser_config_zh.local.toml` - LLM 配置

---

### 2. Chatbot Alicloud (chatbot-alicloud-0908)

基于阿里云 API 的语音聊天机器人。

**特性**：
- 实时语音识别
- 阿里云千问 LLM
- PrimeSpeech TTS
- WebSocket 接口

**启动**：
```bash
cd examples/chatbot-alicloud-0908
export ALIBABA_CLOUD_API_KEY="your-key-here"
./start.sh
```

---

### 3. Conference Debate (conference)

多人 LLM 辩论/会议系统。

**特性**：
- 3人辩论（llm1, llm2, judge）
- Conference Controller 控制发言顺序
- Conference Bridge 消息转发
- 实时 TUI 监控界面

**启动**：
```bash
cd examples/conference
export OPENAI_API_KEY="your-key-here"
./start-debate.sh
```

启动后，在新终端中运行 TUI：
```bash
cd examples/conference
python debate_monitor.py
```

**主要文件**：
- `dataflow-debate-sequential.yml` - 顺序策略辩论
- `debate_monitor.py` - 3面板 TUI 界面
- `viewer.py` - 日志查看器（可选）

---

### 4. Conference Controller (conference-controller)

会议控制器的各种策略示例。

**策略类型**：
1. **Sequential（顺序）**：固定发言顺序
2. **Priority（优先级）**：基于优先级的发言
3. **Ratio（比率）**：基于比率控制发言次数

**启动**：
```bash
cd examples/conference-controller
export OPENAI_API_KEY="your-key-here"
./start.sh
```

脚本会提示选择要运行的 dataflow 文件。

---

### 5. WebSocket Browser (chatbot-openai-websocket-browser)

带浏览器客户端的 WebSocket 聊天机器人示例。

**启动**：
```bash
cd examples/chatbot-openai-websocket-browser
# 查看 README 获取详细启动说明
```
