#!/bin/bash
# Test script for persistent dataflow architecture

echo "==================================="
echo "Testing Persistent Dataflow Setup"
echo "==================================="

# Change to the example directory
cd "$(dirname "$0")"

echo ""
echo "1. Building required components..."
cargo build -p dora-openai-websocket --release
cargo build -p dora-maas-client --release

echo ""
echo "2. Starting WebSocket server (which starts static dataflow)..."
echo "   The server will:"
echo "   - Start static dataflow on startup"
echo "   - Wait for WebSocket connections"
echo "   - Spawn dynamic nodes per connection"
echo ""
echo "Starting server with DATAFLOW_PATH set to local yml file..."

DATAFLOW_PATH="whisper-template-metal.yml" cargo run -p dora-openai-websocket

# Note: To test:
# 1. Run this script
# 2. Wait for "WebSocket server ready" message
# 3. Connect Moly client to ws://localhost:8123
# 4. Observe that wserver and maas-client spawn as dynamic nodes
# 5. Disconnect and reconnect - should be <1s