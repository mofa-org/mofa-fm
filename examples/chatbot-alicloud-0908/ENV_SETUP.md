# Environment Variable Setup for MaaS Client

## Overview
The MaaS client uses the OpenAI API key from environment variables for security. This guide explains how to properly configure it.

## Configuration Methods

### Method 1: Export Environment Variable Before Starting Dataflow (Recommended)

```bash
# Set the environment variable in your shell
export OPENAI_API_KEY="your-actual-api-key-here"

# Start the dataflow (it will inherit the environment variable)
dora start chatbot-staticflow.yml

# In another terminal, start the WebSocket server
cargo run -p dora-openai-websocket -- --name wserver
```

### Method 2: Pass Environment Variable in Dataflow Configuration

Edit `chatbot-staticflow.yml` and add the environment variable to the maas-client node:

```yaml
- id: maas-client
  build: cargo build -p dora-maas-client --release
  path: dynamic
  inputs:
    text: asr/transcription
    text_to_audio: wserver/text
  outputs:
    - text
    - status
    - log
  env:
    CONFIG: maas_mcp_browser_config.toml
    OPENAI_API_KEY: "your-actual-api-key-here"  # Add this line
    LOG_LEVEL: INFO
```

### Method 3: Use a .env File (Development)

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=your-actual-api-key-here
```

Then source it before starting:

```bash
# Load environment variables
source .env

# Start the dataflow
dora start chatbot-staticflow.yml
```

### Method 4: System-wide Environment Variable

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export OPENAI_API_KEY="your-actual-api-key-here"
```

Then reload your shell or run:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Verifying the Configuration

### Check if Environment Variable is Set

```bash
# Verify the environment variable is set
echo $OPENAI_API_KEY

# Should output your API key (be careful not to expose it)
```

### Test the MaaS Client

After starting the dataflow, check the logs:

```bash
# Check maas-client logs
dora logs maas-client

# Look for successful initialization messages
# If you see "Environment variable OPENAI_API_KEY not found", the env var is not properly set
```

## How It Works

The MaaS client configuration file (`maas_mcp_browser_config.toml`) contains:

```toml
api_key = "env:OPENAI_API_KEY"  # This tells the client to read from environment
```

When the MaaS client starts, it:
1. Reads the configuration file
2. Sees `env:OPENAI_API_KEY`
3. Calls `get_env_or_value()` which extracts the environment variable name
4. Looks up the `OPENAI_API_KEY` environment variable
5. Uses that value as the actual API key

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive data
3. **Add .env to .gitignore** if using .env files
4. **Rotate keys regularly** and revoke old ones
5. **Use different keys** for development and production

## Troubleshooting

### "Environment variable OPENAI_API_KEY not found"

This means the environment variable is not set when the maas-client starts. Solutions:
- Make sure you exported the variable in the same shell where you run `dora start`
- Check spelling: `OPENAI_API_KEY` (not `OPENAI_KEY` or other variations)
- If using Method 2, ensure the env section is properly indented in YAML

### "Invalid API key"

This means the environment variable is set but the key is invalid:
- Check you're using the correct API key
- Ensure there are no extra spaces or quotes when setting the variable
- Verify the key works by testing with curl:
  ```bash
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY"
  ```

### API Key Still Visible in Config

If you accidentally committed an API key:
1. Revoke the key immediately in your OpenAI dashboard
2. Generate a new key
3. Follow the git history cleanup steps in the main documentation

## Example Startup Script

Create a `start.sh` script:

```bash
#!/bin/bash

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    echo "Please run: export OPENAI_API_KEY='your-key-here'"
    exit 1
fi

echo "Starting Dora static dataflow..."
dora start chatbot-staticflow.yml

echo "Waiting for nodes to initialize..."
sleep 5

echo "Starting WebSocket server..."
cd ../../node-hub/dora-openai-websocket
cargo run --release -- --name wserver
```

Make it executable:
```bash
chmod +x start.sh
```

Run with:
```bash
export OPENAI_API_KEY="your-key-here"
./start.sh
```