# Dora Pure Dataflow Examples

这个仓库包含了精选的 Dora 框架示例，供实习生学习和参考。

## 📦 仓库结构

```
.
├── examples/           # 示例应用
│   ├── chatbot-alicloud-0908/      # Alicloud 聊天机器人
│   ├── chatbot-openai-0905/        # OpenAI 聊天机器人
│   ├── chatbot-openai-websocket-browser/  # WebSocket 浏览器聊天机器人
│   ├── conference/                 # 会议/辩论示例
│   └── conference-controller/      # 会议控制器示例
└── node-hub/           # Dora 节点（Python）
    ├── dora-asr/                   # 语音识别
    ├── dora-kokoro-tts/            # Kokoro TTS
    ├── dora-primespeech/           # PrimeSpeech TTS
    ├── dora-speechmonitor/         # 语音监控
    └── dora-text-segmenter/        # 文本分段
```

## 🚀 快速开始

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

## 📚 示例说明

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

## 🔧 常见问题

### Q: 找不到 Rust 可执行文件

A: 确保已在 Dora 主仓库中编译了所需的 Rust 节点：
```bash
cd /path/to/dora
cargo build --release
```

然后在启动脚本中指定正确的 `target/release` 目录。

### Q: Python 模块导入错误

A: 确保已安装所有 node-hub 节点：
```bash
cd node-hub/dora-xxx
pip install -e .
```

### Q: API Key 错误

A: 检查环境变量设置：
```bash
echo $OPENAI_API_KEY
echo $ALIBABA_CLOUD_API_KEY
```

### Q: TTS 模型加载失败

A: 需要下载 TTS 模型：
```bash
# 在 Dora 主仓库中
cd examples/model-manager
python download_models.py --download primespeech
python download_models.py --download funasr
```

## 📖 学习路径建议

1. **入门**：从 `chatbot-openai-0905` 开始
   - 理解基本的 dataflow 结构
   - 学习节点间的数据流动
   - 熟悉 WebSocket 接口

2. **进阶**：尝试 `conference`
   - 理解多节点协作
   - 学习 Conference Controller 的策略模式
   - 掌握 TUI 界面开发

3. **深入**：研究 `conference-controller`
   - 对比不同的控制策略
   - 修改参数观察行为变化
   - 尝试实现自定义策略

## 🔗 相关资源

- [Dora 主仓库](https://github.com/dora-rs/dora)
- [Dora 文档](https://dora-rs.github.io/dora/)
- 完整 Dora 代码仓库（包含所有节点和工具）

## 📝 注意事项

1. 这是一个**精选**的示例集合，不包含完整的 Dora 框架
2. 需要访问完整的 Dora 仓库来编译 Rust 节点
3. 某些功能可能需要特定的硬件（如 GPU 加速）
4. API 调用会产生费用，请合理使用

## 🤝 贡献

如果发现问题或有改进建议，欢迎提 Issue 或 Pull Request。

## 📄 许可证

遵循原 Dora 框架的许可证。
