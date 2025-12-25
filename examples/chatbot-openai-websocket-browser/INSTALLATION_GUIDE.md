# Installation Guide for Chatbot OpenAI WebSocket

This guide walks you through setting up and running the Dora voice chat system with WebSocket support and the Moly client interface.

## Prerequisites

- Ubuntu 24.04 or similar Linux distribution
- Python 3.12
- Conda (Anaconda or Miniconda) - see installation instructions below if not installed
- Rust toolchain (rustc, cargo)
- Git with LFS support
- CUDA toolkit (optional, for GPU acceleration)
- Sufficient disk space (~50GB for models)

### Installing Conda (if not already installed)

If you don't have conda installed, choose ONE of the following options:

**OPTION A: Install Miniconda (RECOMMENDED - lightweight, ~250MB)**

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Run the installer (press Enter for defaults, type 'yes' when asked)
bash Miniconda3-latest-Linux-x86_64.sh

# Activate conda in your current session
source ~/.bashrc

# Verify installation
conda --version
```

**OPTION B: Install Anaconda (Full distribution, ~3GB)**

```bash
# Download Anaconda installer
wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh

# Run the installer (press Enter for defaults, type 'yes' when asked)
bash Anaconda3-2024.06-1-Linux-x86_64.sh

# Activate conda in your current session
source ~/.bashrc

# Verify installation
conda --version
```

After installation, you should see "(base)" in your terminal prompt.

## Step 1: Setup Isolated Environment

Navigate to the setup directory and run the isolated environment setup:

```bash
cd examples/setup-new-chatbot
./setup_isolated_env.sh
```

This script will:
- Install all system dependencies (gcc, g++, gfortran, build-essential, libopenblas, openssl, portaudio, git-lfs, ffmpeg)
- Create a conda environment named `dora_voice_chat` with Python 3.12
- Install all required Python packages with correct versions

**Important**: Activate the conda environment for ALL terminals you'll use:

```bash
conda activate dora_voice_chat
```

## Step 2: Install All Packages (Ubuntu/Linux)

You have two options for installing the required packages:

#### Option A: Automated Installation (Recommended)

Run the all-in-one installation script:

```bash
# Run the installation script
cd ../setup-new-chatbot
./install_all_packages.sh
```

This script will automatically:
- Install all Dora Python packages in editable mode
- Install Rust (if not already installed)
- Install Dora CLI
- Build all Rust-based nodes (dora-maas-client, dora-openai-websocket)

#### Option B: Manual Step-by-Step Installation

If you prefer to install components manually or need more control:

```bash
# 1. Activate conda environment first
conda activate dora_voice_chat

# 2. Install all Dora packages in editable mode
cd ../..  # Go to dora root directory
pip install -e node-hub/dora-primespeech
pip install -e node-hub/dora-asr
pip install -e node-hub/dora-speechmonitor
pip install -e node-hub/dora-text-segmenter

# 3. Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 4. Install Dora CLI
cargo install dora-cli --locked

# 5. Build Rust-based nodes
cargo build --release -p dora-maas-client
cargo build --release -p dora-openai-websocket
```

## Step 3: Download All Models

Navigate to the model-manager directory and download all required models.

### Option A: Automated Download (Recommended)

Use the all-in-one download script:

```bash
# Make sure conda environment is activated
conda activate dora_voice_chat

cd ../model-manager

# Run the download all script
./download_all_models.sh
```

This script will:
- Download FunASR models for speech recognition
- Download complete PrimeSpeech package (base models + G2PW + all voices)
- Verify all downloads
- Optionally convert models to ONNX format for better performance

### Option B: Manual Download

If you prefer to download models individually:

```bash
# Make sure conda environment is activated
conda activate dora_voice_chat

cd ../model-manager

# Download ASR models (FunASR for Chinese/English)
python download_models.py --download funasr

# Download complete PrimeSpeech TTS package (base models + G2PW + all voices)
python download_models.py --download primespeech

# Alternative: Download PrimeSpeech components separately if needed
# python download_models.py --download primespeech-base  # Base models only
# python download_models.py --download g2pw              # G2PW model only
# python download_models.py --voice all                  # All voice files only

# Or download specific voice (e.g., Doubao)
# python download_models.py --voice Doubao

# List available voices
python download_models.py --list-voices

# List all downloaded models
python download_models.py --list
```

### Convert Models to ONNX (Optional, for optimization)

```bash
# Make sure conda environment is activated
conda activate dora_voice_chat

# Convert all models to ONNX format for better performance
python convert_to_onnx.py --convert all
```

## Step 4: Validate ASR and PrimeSpeech

Return to the setup directory and run validation tests to ensure everything is working:

```bash
cd ../setup-new-chatbot

# Validate ASR (Speech Recognition)
cd asr-validation
python test_basic_asr.py

# If you have GPU support, you can also run:
USE_GPU=true python benchmark_gpu.py
```

### ASR Configuration Options

The ASR node supports multiple engines and configurations:

| Variable | Values | Description | Default |
|----------|--------|-------------|---------|
| `USE_GPU` | `"true"/"false"` | Enable GPU acceleration | `"false"` |
| `ASR_ENGINE` | `"funasr"/"whisper"/"auto"` | Select ASR engine | `"auto"` |
| `LANGUAGE` | `"zh"/"en"/"auto"` | Target language | `"auto"` |
| `ENABLE_PUNCTUATION` | `"true"/"false"` | Add punctuation | `"true"` |

### Expected Performance (with GPU)

Based on RTX 4090 testing with 17.35s Chinese audio:
- **CPU Processing**: 0.640s (27.1x real-time)
- **GPU Processing**: 0.282s (61.6x real-time)
- **GPU Speedup**: 2.27x faster
- **Memory Usage**: ~2GB VRAM

### Validate PrimeSpeech (Text-to-Speech)

```bash
cd ..
cd primespeech-validation
python test_tts_direct.py

cd ../..
```


### PrimeSpeech Configuration

```bash
# Environment variables for TTS
export PRIMESPEECH_MODEL_DIR=$HOME/.dora/models/primespeech
export VOICE_NAME=Doubao        # Available: Doubao, Luo Xiang, Yang Mi, etc.
export TEXT_LANG=zh             # zh for Chinese, en for English
export USE_GPU=false            # Set to true for GPU acceleration
export SPEED_FACTOR=1.0         # 0.8-1.2 range for speed adjustment
```

### Troubleshooting TTS Issues

If PrimeSpeech tests fail:

```bash
# Check if G2PW model is downloaded
ls -lh ~/.dora/models/primespeech/G2PWModel/

# If missing, download it
cd ../../model-manager
python download_models.py --download primespeech-base

# Check voice files
ls -lh ~/.dora/models/primespeech/moyoyo/

# If missing specific voice
python download_models.py --voice Doubao
```

For detailed troubleshooting and optimization tips, see `setup-new-chatbot/primespeech-validation/README.md`.

### Troubleshooting ASR Issues

If ASR tests fail:

```bash
# Check if models are properly downloaded (should be >100MB)
ls -lh ~/.dora/models/asr/funasr/*/model*

# Test GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Debug engine selection
python -c "
import os
os.environ['USE_GPU'] = 'true'
from dora_asr.manager import ASRManager
m = ASRManager()
print(f'Engine: {m._engine_classes[\"funasr\"].__name__}')
"
```

All tests should pass. If any fail, check the error messages and ensure models are properly downloaded. For detailed troubleshooting, see the ASR validation README in `setup-new-chatbot/asr-validation/README.md`.

## Step 5: Configure OpenAI API Key

Navigate to the chatbot example and configure your OpenAI API key:

```bash
cd chatbot-openai-websocket-browser

# Edit the configuration file
nano maas_config.toml  # or use your preferred editor
```

Find the line with `api_key` and add your OpenAI API key:

```toml
[[providers]]
id = "openai"
kind = "openai"
api_key = "sk-your-actual-openai-api-key-here"  # Replace with your real key
# api_key = "env:OPENAI_API_KEY"  # Or use environment variable
```

Save the file.

## Step 6: Install Playwright MCP Server (for Browser Automation Tools)

The Playwright MCP server enables browser automation through voice commands. Install it using npm:

```bash
# Install the Playwright MCP server globally
npm install -g @playwright/mcp

# Or use npx to run it directly (as configured in the TOML file)
npx @playwright/mcp --help

# The server will automatically download browser binaries when first run
```

This MCP server provides tools for:
- **Browser Navigation**: Open URLs, click elements, fill forms
- **Screenshots**: Capture full page or specific elements
- **Content Extraction**: Get page text, HTML, or specific data
- **Automation**: Complex multi-step web interactions

The Playwright MCP server is already configured in `maas_mcp_browser_config.toml`:

```toml
[[mcp.servers]]
name = "playwright"
protocol = "stdio"  
command = "npx"
args = [
    "-y",
    "@playwright/mcp@latest"
]
```

For more information about the Playwright MCP server, see: https://github.com/microsoft/playwright-mcp

## Step 7: Build All Dora Nodes

Build all the required Dora nodes using the template:

```bash
# Make sure you're in the chatbot-openai-websocket-browser directory
cd /home/dspfac/home/dora/examples/chatbot-openai-websocket-browser

# Build all nodes defined in the template
dora build whisper-template-metal.yml

# This will build:
# - dora-openai-websocket (Rust WebSocket server)
# - dora-maas-client (Rust MaaS client)
# - dora-speechmonitor (Python speech detection)
# - dora-asr (Python ASR)
# - dora-text-segmenter (Python text chunking)
# - dora-primespeech (Python TTS)
```

## Step 8: Run WebSocket Server

Start the WebSocket server that will handle voice chat sessions:

```bash
# Make sure you're in the dora root directory
cargo run -p dora-openai-websocket
```

You should see:
```
Server started, listening on 0.0.0.0:8123
```

Keep this terminal running.

## Step 9: Run Moly Client

In a new terminal (remember to activate conda environment):

```bash
# Navigate to your Moly repository
cd ~/moly  # Adjust path to your Moly repo location

# Build and run Moly in release mode
cargo run --release
```

The Moly client will start and open in your default browser.

## Step 10: Configure Moly Provider

In the Moly client interface:

1. Look for the provider settings (usually a gear icon or settings menu)
2. Find "Dora Realtime" provider
3. Configure as follows:
   - WebSocket URL: `localhost:8123`
   - API Key: Enter any text (e.g., "fake-key") - this is just a placeholder
4. Save the configuration

## Step 11: Create New Chat Session

In the Moly client:

1. Click "New Chat" or "+" to create a new chat session
2. You should see a microphone/talk icon in the bottom right corner
3. Click the talk icon to launch the voice interface

## Step 12: Start Voice Conversation

1. Click the "Start" button to begin the conversation
2. In the WebSocket server terminal, you should see:
   - "Client connected"
   - "WebSocket upgrade successful"
   - "✅ Dataflow started successfully"
   - "✅ Dora node initialized successfully"

This confirms the session is active and all Dora nodes are connected.

## Step 13: Have a Conversation

1. Speak into your microphone
2. You should see the following states in Moly:
   - "Connecting" - Establishing WebSocket connection
   - "Loading" - Initializing the session
   - "Listening" - Ready to detect speech
   - "Speech detected" - When you start speaking
   - "Response generated" - When the AI completes processing
3. The conversation flow:
   - Your transcribed text appears
   - The AI's response text displays
   - Audio playback of the response

**Note**: Response generation may take a while on weaker machines. First response might be slower as models load into memory.

## Step 14: Managing Sessions

- Click "Stop" to end the current conversation
- Click "Start" again to launch a new WebSocket session
- Each new session creates a fresh dataflow with unique node IDs

## Troubleshooting

### If ASR (Speech Recognition) isn't working:
```bash
# Check if models are properly downloaded
ls -lh ~/.dora/models/asr/funasr/
# Files should be >100MB, not small pointer files

# Test ASR directly
cd examples/setup-new-chatbot/asr-validation
python test_basic_asr.py
```

### If TTS (Text-to-Speech) isn't working:
```bash
# Check PrimeSpeech models
ls -lh ~/.dora/models/primespeech/

# Test TTS directly
cd examples/setup-new-chatbot/primespeech-validation
python test_tts_direct.py
```

### If WebSocket connection fails:
- Ensure the server is running on port 8123
- Check firewall settings
- Try restarting both the WebSocket server and Moly client
- Check the WebSocket server logs for error messages

### If nodes fail to connect:
- Make sure `dora up` is running (coordinator and daemon)
- Check that all nodes built successfully
- Review logs: `dora logs <dataflow-id> <node-name>`

## Performance Tips

1. **GPU Acceleration**: If you have an NVIDIA GPU, set `USE_GPU=true` in the dataflow environment variables for faster ASR processing

2. **Model Loading**: First run will be slower as models load. Subsequent runs will be faster.

3. **Network**: Ensure stable network connection if using cloud-based OpenAI models

4. **Memory**: Ensure at least 8GB RAM available for smooth operation

## Additional Features

### Browser Automation
If you configured Playwright in Step 5, you can use voice commands to control web browsing:
- "Open Google and search for..."
- "Take a screenshot of the page"
- "Click on the first link"

### Weather Information
The system includes a mock weather server that can respond to weather queries.

### Multiple Languages
The system supports both Chinese and English. Language is auto-detected from your speech.

## Next Steps

- Customize the system prompt in the TOML config files
- Try different TTS voices by modifying the PrimeSpeech settings
- Experiment with different LLM models
- Add custom MCP tools for extended functionality

For more details, see the main README and individual component documentation.