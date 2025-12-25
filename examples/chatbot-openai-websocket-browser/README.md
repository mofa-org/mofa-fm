# OpenAI WebSocket Browser Example

This example demonstrates a voice chat system using WebSocket for browser/client communication, with cloud-based AI models (MaaS) instead of local models.

## Architecture

The system uses a WebSocket server (`dora-openai-websocket`) that:
1. Accepts connections from clients (like Moly)
2. Dynamically spawns a Dora dataflow based on the template
3. Routes audio and text between the client and the dataflow

## Prerequisites

1. Ensure you have built the WebSocket server:
```bash
cd ../../node-hub/dora-openai-websocket
cargo build --release -p dora-openai-websocket
```

2. Make sure all required Dora nodes are installed:
```bash
# Install Python nodes
pip install -e ../../node-hub/dora-asr
pip install -e ../../node-hub/dora-speechmonitor  
pip install -e ../../node-hub/dora-text-segmenter
pip install -e ../../node-hub/dora-primespeech

# Build Rust nodes
cargo build --release -p dora-maas-client
```

3. Ensure models are in place:
- ASR models: `/Users/yuechen/.dora/models/asr`
- PrimeSpeech models: `/Users/yuechen/.dora/models/primespeech`

## Configuration

The system uses `whisper-template-metal.yml` as a template. When a client connects, the WebSocket server:
1. Receives a session configuration from the client
2. Replaces `NODE_ID` in the template with a unique server ID (e.g., `server-12345`)
3. Creates a new dataflow YAML file (e.g., `whisper-12345.yml`)
4. Starts the dataflow automatically

### MaaS Configuration

1. Copy the example configuration file:
```bash
cp maas_mcp_browser_config.toml.example maas_mcp_browser_config.toml
```

2. Edit `maas_mcp_browser_config.toml` and set your OpenAI API key:
   - Either set the `OPENAI_API_KEY` environment variable
   - Or replace `env:OPENAI_API_KEY` with your actual API key

3. The configuration path can be customized using the `MAAS_CONFIG_PATH` environment variable:
```bash
# Use a custom config file location
export MAAS_CONFIG_PATH="/path/to/your/config.toml"
cargo run -p dora-openai-websocket
```
If not set, it defaults to `maas_mcp_browser_config.toml` in the current directory.

## Running the System

### Step 1: Start the Mock Weather Server (Optional)

If you want to test browser automation features:
```bash
python mock_weather_server.py
```

### Step 2: Start the WebSocket Server

From this directory:
```bash
cargo run -p dora-openai-websocket
```

You should see output like:
```
Server started, listening on 0.0.0.0:8123
```

The server is now waiting for WebSocket connections on port 8123.

### Step 3: Connect with Moly Client

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

## Troubleshooting

### "Connection reset without closing" error
- Check that the WebSocket server is running
- Verify the template file exists: `whisper-template-metal.yml`
- Check server logs for any parsing errors

### No audio output
- Verify PrimeSpeech models are installed
- Check ASR is receiving audio (view logs)
- Ensure audio sample rates are correct (24kHz input, 24kHz output)

### MaaS not responding
- Check `maas_mcp_browser_config.toml` has valid API keys
- Verify network connectivity to cloud providers
- Check MaaS client logs for errors

## File Structure

```
openai-websocket-browser/
├── README.md                           # This file
├── whisper-template-metal.yml          # Dataflow template
├── maas_mcp_browser_config.toml       # MaaS configuration
├── mock_weather_server.py             # Mock server for testing
└── whisper-*.yml                       # Generated dataflow files (created at runtime)
```

## Notes

- Each client connection creates a separate dataflow instance
- The `NODE_ID` placeholder in the template is replaced with a unique ID
- Generated dataflow files (whisper-*.yml) can be deleted after use
- The system supports multiple concurrent connections
