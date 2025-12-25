# Chatbot Alibaba Cloud WebSocket Example

This example demonstrates a voice chat system using WebSocket for browser/client communication, with Alibaba Cloud AI models (Qwen, DeepSeek, GLM, Kimi) via the MaaS client.

## Architecture

The system uses a WebSocket server (`dora-openai-websocket`) that:
1. Accepts connections from clients (like Moly)
2. Dynamically spawns a Dora dataflow based on the template
3. Routes audio and text between the client and the dataflow

## System Requirements

- Ubuntu 24.04 or similar Linux distribution (macOS also supported)
- Python 3.12
- Conda (Anaconda or Miniconda)
- Rust toolchain (rustc, cargo)
- Git with LFS support
- CUDA toolkit (optional, for GPU acceleration)
- Sufficient disk space (~50GB for models)

## Quick Start

### Step 1: Setup Environment

Navigate to the setup directory and run the isolated environment setup:

```bash
cd ../setup-new-chatbot
./setup_isolated_env.sh
```

This script will:
- Install all system dependencies
- Create a conda environment named `dora_voice_chat` with Python 3.12
- Install all required Python packages with correct versions

**Important**: Activate the conda environment for ALL terminals you'll use:

```bash
conda activate dora_voice_chat
```

### Step 2: Install All Packages

Run the all-in-one installation script:

```bash
# From setup-new-chatbot directory
./install_all_packages.sh
```

This will automatically:
- Install all Dora Python packages in editable mode
- Install Rust (if not already installed)
- Install Dora CLI
- Build all Rust-based nodes (dora-maas-client, dora-openai-websocket)

### Step 3: Download All Models

Use the automated download script:

```bash
cd ../model-manager
./download_all_models.sh
```

This will:
- Download FunASR models for speech recognition
- Download complete PrimeSpeech package (base models + G2PW + all voices)
- Verify all downloads
- Optionally convert models to ONNX format for better performance

### Step 4: Configure MaaS

1. Copy the example configuration file:
```bash
cd ../chatbot-alicloud-0908
cp maas_mcp_browser_config.toml.example maas_mcp_browser_config.toml
```

2. Set your API keys:
   - **Alibaba Cloud**: Set the `ALIBABA_CLOUD_API_KEY` environment variable:
     ```bash
     export ALIBABA_CLOUD_API_KEY="sk-your-alibaba-cloud-key"
     ```
   - **OpenAI (optional)**: Set the `OPENAI_API_KEY` environment variable:
     ```bash
     export OPENAI_API_KEY="sk-your-openai-key"
     ```

3. The configuration path can be customized using the `MAAS_CONFIG_PATH` environment variable:
```bash
# Use a custom config file location, export MAAS_CONFIG_PATH="maas_mcp_browser_config.toml"
export MAAS_CONFIG_PATH="/path/to/your/config.toml" 


cargo run -p dora-openai-websocket
```
If not set, it defaults to `maas_mcp_browser_config.toml` in the current directory.

### Step 5: Build and Run

最快的方式是使用交互式脚本：

```bash
./start.sh
```

脚本会依次确认：
1. Dora 根目录与 `target/release` 可执行文件位置
2. MaaS 配置文件路径 (`maas_mcp_browser_config.toml`)
3. `ALIBABA_CLOUD_API_KEY`（必填）与可选的 `OPENAI_API_KEY`
4. PrimeSpeech/FunASR 模型是否已下载（若缺失会给出下载命令）

如果你更喜欢手动步骤，可以继续使用原始命令：

```bash
# Build all nodes defined in the template
dora build chatbot-staticflow.yml

# Start the static dataflow
dora start chatbot-staticflow.yml

# Start the WebSocket server
cargo run -p dora-openai-websocket -- --name wserver
```

WebSocket 服务器启动后会显示：
```
Server started, listening on 0.0.0.0:8123
```

### Step 6: Connect with Moly Client

1. In a new terminal, navigate to your Moly repository and run:
```bash
cargo run --release
```

2. In the Moly client interface:
   - Configure the "Dora Realtime" provider
   - WebSocket URL: `localhost:8123`
   - API Key: Enter any text (e.g., "fake-key") - this is just a placeholder
   - **System Prompt**: Customize the system prompt in the provider settings
     - **For Chinese users**: Use a Chinese system prompt (e.g., "你是一个友好的助手，请用中文回答所有问题。") as the current Chinese TTS has issues generating English speech
     - **For English users**: Use the default English system prompt

3. Create a new chat session and click the talk icon to start voice conversation

**Important Note for Chinese Users**: The current Chinese TTS voices have limitations generating English speech. Please ensure your system prompt in Moly is set to respond in Chinese only to avoid TTS errors.

## Data Flow

1. **Client → Server**: 
   - Audio data via `input_audio_buffer.append` 
   - Text/greetings via `response.create`

2. **Server → Dataflow**:
   - Audio → Speech Monitor → ASR → MaaS Client
   - Greetings → MaaS Client (via `text_to_audio` input)

3. **Dataflow → Server → Client**:
   - MaaS response → Text Segmenter → PrimeSpeech TTS → Audio output

## Available Alibaba Cloud Models

The system is configured with multiple Alibaba Cloud models:

### Qwen Series
- **qwen-max**: Most capable Qwen model with advanced reasoning
- **qwen-plus**: Enhanced performance model, balanced cost/quality
- **qwen-turbo**: Fast and cost-effective for general tasks
- **qwen-long**: Specialized for long context (up to 10M tokens)
- **qwen-vl-max**: Vision-language model for image understanding
- **qwen-vl-plus**: Enhanced vision-language capabilities
- **qwen-coder-turbo**: Fast code generation
- **qwen-coder-plus**: Advanced code generation and understanding

### DeepSeek Models
- **deepseek-v3**: Latest DeepSeek chat model
- **deepseek-v3.1**: Updated version with improvements
- **deepseek-r1-0528**: DeepSeek reasoning model

### Other Models
- **glm-4.5**: GLM series model from Zhipu AI
- **Moonshot-Kimi-K2-Instruct**: Kimi model from Moonshot AI

### Switching Models

To switch models, edit `maas_mcp_browser_config.toml`:
```toml
default_model = "qwen-max"  # Change to any available model ID
```

Or dynamically in conversation:
- "Switch to qwen-plus model"
- "Use deepseek-v3 for coding"

## Configuration Options

### ASR Configuration

| Variable | Values | Description | Default |
|----------|--------|-------------|---------|
| `USE_GPU` | `"true"/"false"` | Enable GPU acceleration | `"false"` |
| `ASR_ENGINE` | `"funasr"/"whisper"/"auto"` | Select ASR engine | `"auto"` |
| `LANGUAGE` | `"zh"/"en"/"auto"` | Target language | `"auto"` |
| `ENABLE_PUNCTUATION` | `"true"/"false"` | Add punctuation | `"true"` |

### PrimeSpeech TTS Configuration

```bash
export PRIMESPEECH_MODEL_DIR=$HOME/.dora/models/primespeech
export VOICE_NAME=Doubao        # Available: Doubao, Luo Xiang, Yang Mi, etc.
export TEXT_LANG=zh             # zh for Chinese, en for English
export USE_GPU=false            # Set to true for GPU acceleration
export SPEED_FACTOR=1.0         # 0.8-1.2 range for speed adjustment
```

## Performance Benchmarks

### ASR Performance (with RTX 4090)
- **CPU Processing**: 0.640s (27.1x real-time)
- **GPU Processing**: 0.282s (61.6x real-time)
- **GPU Speedup**: 2.27x faster
- **Memory Usage**: ~2GB VRAM

## Advanced Features

### Browser Automation (Optional)

Install the Playwright MCP server for browser control via voice:

```bash
npm install -g @playwright/mcp
```

This enables commands like:
- "Open Google and search for..."
- "Take a screenshot of the page"
- "Click on the first link"

### Multiple Language Support

The system supports both Chinese and English with automatic language detection.

## Troubleshooting

### ASR Issues
```bash
# Check if models are properly downloaded
ls -lh ~/.dora/models/asr/funasr/
# Files should be >100MB, not small pointer files

# Test ASR directly
cd ../setup-new-chatbot/asr-validation
python test_basic_asr.py
```

### TTS Issues
```bash
# Check PrimeSpeech models
ls -lh ~/.dora/models/primespeech/

# Test TTS directly
cd ../setup-new-chatbot/primespeech-validation
python test_tts_direct.py
```

### WebSocket Connection Issues
- Ensure the server is running on port 8123
- Check firewall settings
- Try restarting both the WebSocket server and Moly client
- Check the WebSocket server logs for error messages

### Node Connection Issues
- Make sure `dora up` is running (coordinator and daemon)
- Check that all nodes built successfully
- Review logs: `dora logs <dataflow-id> <node-name>`

## File Structure

```
chatbot-openai-0905/
├── README.md                           # This file
├── chatbot-staticflow.yml             # Main dataflow configuration
├── maas_mcp_browser_config.toml.example  # Example MaaS configuration
├── mock_weather_server.py             # Mock server for testing
└── whisper-*.yml                       # Generated dataflow files (runtime)
```

## Performance Tips

1. **GPU Acceleration**: Set `USE_GPU=true` in environment variables for faster ASR processing
2. **Model Loading**: First run will be slower as models load. Subsequent runs will be faster
3. **Network**: Ensure stable network connection for cloud-based OpenAI models
4. **Memory**: Ensure at least 8GB RAM available for smooth operation

## Next Steps

- Customize the system prompt in the TOML config files
- Try different TTS voices by modifying the PrimeSpeech settings
- Experiment with different LLM models
- Add custom MCP tools for extended functionality

For more details, see individual component documentation in the node-hub directory.
