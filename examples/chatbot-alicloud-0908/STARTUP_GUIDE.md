# Moly Client + Dora WebSocket Server Startup Guide

## Overview
This guide explains how to start the Dora static dataflow and WebSocket server for use with the Moly client (OpenAI Realtime API compatible).

## Prerequisites
- Dora CLI installed and configured
- All required models downloaded (ASR, TTS)
- Python and Rust environments set up

## Startup Sequence

### Step 1: Start the Static Dataflow
The static dataflow contains persistent audio processing nodes (speech-monitor, ASR, TTS, etc.) that must be running before client connections.

```bash
# Navigate to the chatbot example directory
cd /Users/yuechen/home/fresh/dora/examples/chatbot-openai-0905

# Start the static dataflow
dora start chatbot-staticflow.yml
```

Wait for confirmation that all nodes are running. You should see output like:
```
✅ speech-monitor started
✅ asr started
✅ maas-client started
✅ text-segmenter started
✅ primespeech started
```

### Step 2: Start the WebSocket Server
Once the static dataflow is running, start the WebSocket server that handles Moly client connections.

```bash
# In a new terminal, navigate to the Wechatbot-openai-0905 directory

# Run the WebSocket server
cargo run -p dora-openai-websocket -- --name wserver```

The server will start on port 8000 by default. You should see:
```
🚀 WebSocket server listening on: 0.0.0.0:8123
```

### Step 3: Connect Moly Client
Now you can connect your Moly client to the WebSocket server:

```
ws://localhost:8123
```

The server will:
1. Accept the connection
2. Send an initial greeting in Chinese
3. Start listening for voice input
4. Process speech with proper VAD (3-second silence for question completion)
5. Generate and stream responses back

## Important Notes

### Startup Order
⚠️ **CRITICAL**: You MUST start the static dataflow BEFORE the WebSocket server. The server expects these nodes to be running:
- `speech-monitor` - Voice activity detection
- `asr` - Speech recognition
- `maas-client` - LLM processing
- `text-segmenter` - Response chunking
- `primespeech` - Text-to-speech

### Troubleshooting

#### "Multiple dataflows contain dynamic node id wserver"
This error means you're trying to start the WebSocket server before the static dataflow, or trying to start multiple instances. Solution:
1. Stop all Dora processes: `dora stop`
2. Start static dataflow first: `dora start chatbot-staticflow.yml`
3. Then start WebSocket server: `cargo run --release`

#### ASR Not Loading
Check that the ASR models are properly downloaded:
```bash
ls ~/.dora/models/asr/funasr/
```

#### Moly Stuck in Listening Mode
This usually means:
1. Audio is not reaching the speech-monitor node
2. Microphone input issues on the client side

Check logs for audio frame reception:
```bash
# Check if wserver is receiving audio
# Look for: "📊 Audio frame received from Moly"

# Check if speech-monitor is detecting speech
# Look for: "Speech STARTED" messages
```

## Configuration

### Environment Variables
You can customize behavior with environment variables in `chatbot-staticflow.yml`:

```yaml
# VAD Settings
QUESTION_END_SILENCE_MS: 3000  # Time to wait for question completion
USER_SILENCE_THRESHOLD_MS: 1500  # Time to detect speech end
VAD_THRESHOLD: 0.6  # Voice activity detection sensitivity

# ASR Settings
ASR_ENGINE: funasr  # Or whisper
LANGUAGE: zh  # Chinese (or en for English)

# TTS Settings
VOICE_NAME: Doubao  # TTS voice selection
```

## Monitoring

### Check Node Status
```bash
# View all running nodes
dora list

# Check specific node logs
dora logs speech-monitor
dora logs asr
```

### WebSocket Server Logs
The server provides detailed logging:
- `❓ Question ended detected` - Full sentence detected, triggering LLM
- `📝 Transcription received` - ASR output received
- `🤖 LLM response received` - Response from AI model
- `🔊 Audio frame sent to Moly` - TTS audio being streamed

## Stopping the System

### Graceful Shutdown
```bash
# Stop WebSocket server
# Press Ctrl+C in the terminal running cargo

# Stop static dataflow
dora stop chatbot-staticflow.yml

# Or stop all Dora processes
dora stop --all
```

## Quick Start Script
Create a `start.sh` script for convenience:

```bash
#!/bin/bash
echo "Starting Dora static dataflow..."
dora start chatbot-staticflow.yml

echo "Waiting for nodes to initialize..."
sleep 5

echo "Starting WebSocket server..."
cd ../../node-hub/dora-openai-websocket
cargo run --release
```

Make it executable: `chmod +x start.sh`

## Support
For issues or questions, refer to:
- CODE_CHANGES.md - Detailed technical changes
- CLAUDE.md - Project context and architecture
- Dora documentation - Framework reference