# Chatbot OpenAI WebSocket Example

This example demonstrates a voice chat system using WebSocket for browser/client communication, with cloud-based AI models (MaaS) instead of local models.

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

### Step 2: Install All Packages and Convert the ONXX Models

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
- Convert models to ONNX format for better performance
```bash
cd ../model-manager
./python convert_to_onnx.py --convert all
```
### Step 4: Configure MaaS

1. Copy the example configuration file:
```bash
cd ../chatbot-openai-0905
cp maas_mcp_browser_config.toml.example maas_mcp_browser_config.toml
```

2. Edit `maas_mcp_browser_config.toml` and set your OpenAI API key:
   - Either set the `OPENAI_API_KEY` environment variable
   - Or replace `env:OPENAI_API_KEY` with your actual API key

3. The configuration path can be customized using the `MAAS_CONFIG_PATH` environment variable:
```bash
# Use a custom config file location, export MAAS_CONFIG_PAT="maas_mcp_browser_config.toml"
export MAAS_CONFIG_PATH="/path/to/your/config.toml" 

cargo run -p dora-openai-websocket
```
If not set, it defaults to `maas_mcp_browser_config.toml` in the current directory.

### Step 5: Build and Run

```bash
# Build all nodes defined in the template
dora build chatbot-staticflow.yml

# start the static dataflow
dora start chatbot-staticflow.yml

# Start the WebSocket server
cargo run -p dora-openai-websocket -- --name wserver
```

You should see:
```
Server started, listening on 0.0.0.0:8123
```

### Step 6: Connect with Moly Client

1. Open the Moly client application
2. Configure the "Dora Realtime" provider:
   - WebSocket URL: `ws://localhost:8123` (or `ws://0.0.0.0:8123`)
   - API Key: Enter any text (e.g., "fake-key") - this is just a placeholder
   - **System Prompt**: Customize the system prompt in the provider settings
     - **For Chinese users**: Use a Chinese system prompt (e.g., "你是一个友好的助手，请用中文回答所有问题。") as the current Chinese TTS has issues generating English speech
     - **For English users**: Use the default English system prompt
3. Start a conversation

**Important Note for Chinese Users**: The current Chinese TTS voices have limitations generating English speech. Please ensure your system prompt in Moly is set to respond in Chinese only to avoid TTS errors.

When Moly connects:
- It sends a `session.update` message with configuration
- The server creates a new dataflow instance
- Moly can send an initial greeting via `response.create` 
- The greeting is routed to the MaaS client which generates a response

## Data Flow

1. **Client → Server**: 
   - Audio data via `input_audio_buffer.append` 
   - Text/greetings via `response.create`

2. **Server → Dataflow**:
   - Audio → Speech Monitor → ASR → MaaS Client
   - Greetings → MaaS Client (via `text_to_audio` input)

3. **Dataflow → Server → Client**:
   - MaaS response → Text Segmenter → PrimeSpeech TTS → Audio output

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


## MCP Features

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