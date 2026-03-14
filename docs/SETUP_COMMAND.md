# SmolClaw Setup Command

## Quick Start

```bash
# Quick setup with Hugging Face (recommended)
smolclaw setup --hf-token YOUR_HF_TOKEN

# Setup and start gateway
smolclaw setup --hf-token YOUR_HF_TOKEN --start-gateway

# Full setup with all options
smolclaw setup \
    --provider huggingface \
    --model Qwen/Qwen2.5-7B-Instruct \
    --base-url https://router.huggingface.co/v1 \
    --hf-token YOUR_TOKEN \
    --headless \
    --gateway-host 127.0.0.1 \
    --gateway-port 8765 \
    --start-gateway \
    --verbose
```

## Command Reference

### `smolclaw setup`

One-command setup with all configuration options.

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--provider` | `huggingface` | LLM provider (currently only huggingface) |
| `--model` | `Qwen/Qwen2.5-7B-Instruct` | Model name to use |
| `--base-url` | `https://router.huggingface.co/v1` | API base URL |
| `--api-key` | (empty) | API key or token |
| `--hf-token` | (empty) | Hugging Face token |
| `--headless` | `False` | Run browser in headless mode |
| `--gateway-host` | `127.0.0.1` | Gateway host |
| `--gateway-port` | `8765` | Gateway port |
| `--start-gateway` | `True` | Start gateway after setup |
| `--verbose`, `-v` | `False` | Verbose output |

#### Examples

**1. Minimal Setup (Quick Start)**
```bash
smolclaw setup --hf-token YOUR_TOKEN
```
Creates:
- `~/.smolclaw/` directory structure
- Configuration with default model (Qwen2.5-7B-Instruct)
- Hugging Face authentication

**2. Setup with Custom Model**
```bash
smolclaw setup \
    --hf-token YOUR_TOKEN \
    --model mistralai/Mistral-7B-Instruct-v0.3
```

**3. Setup for Headless Environment (Server/CI)**
```bash
smolclaw setup \
    --hf-token YOUR_TOKEN \
    --headless \
    --no-start-gateway
```

**4. Setup with Custom Gateway**
```bash
smolclaw setup \
    --hf-token YOUR_TOKEN \
    --gateway-host 0.0.0.0 \
    --gateway-port 9000 \
    --start-gateway
```

**5. Full Setup with Verbose Output**
```bash
smolclaw setup \
    --provider huggingface \
    --model Qwen/Qwen2.5-7B-Instruct \
    --base-url https://router.huggingface.co/v1 \
    --hf-token YOUR_TOKEN \
    --headless \
    --gateway-host 127.0.0.1 \
    --gateway-port 8765 \
    --start-gateway \
    --verbose
```

## What Setup Does

### Step 1: Create Directory Structure
```
~/.smolclaw/
├── config/
│   ├── config.json       # Main configuration
│   ├── gateway.pid       # Gateway process ID
│   └── gateway.log       # Gateway logs
├── workplace/            # Default working area
├── mcp/                  # MCP add-ons
├── SOUL.md              # Agent personality
├── TOOLS.md             # Available tools
└── SKILLS.md            # Reusable skills
```

### Step 2: Configure Model Provider
- Sets provider (Hugging Face)
- Configures model name
- Sets API base URL

### Step 3: Authenticate (Optional)
- Logs into Hugging Face with provided token
- Adds token to git credential helper (optional)

### Step 4: Save Configuration
Configuration saved to `~/.smolclaw/config/config.json`:
```json
{
  "provider": "huggingface",
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "base_url": "https://router.huggingface.co/v1",
  "api_key": "***",
  "hf_token": "***",
  "headless": false,
  "gateway_host": "127.0.0.1",
  "gateway_port": 8765
}
```

### Step 5: Start Gateway (Optional)
- Starts websocket gateway in background
- Creates PID file
- Logs to `~/.smolclaw/config/gateway.log`

## Output

### Successful Setup
```
============================================================
  SmolClaw Setup
============================================================

[1/5] Creating SmolClaw home directory...
  ✓ Created: /Users/you/.smolclaw
  ✓ Workplace: /Users/you/.smolclaw/workplace
  ✓ MCP directory: /Users/you/.smolclaw/mcp

[2/5] Configuring model provider...
  Provider: Hugging Face
  Model: Qwen/Qwen2.5-7B-Instruct
  Base URL: https://router.huggingface.co/v1

[3/5] Authenticating with Hugging Face...
  ✓ Hugging Face login successful

[4/5] Saving configuration...
  ✓ Configuration saved to: /Users/you/.smolclaw/config/config.json

[5/5] Starting gateway...
  ✓ Gateway started (pid=12345)
  ✓ Endpoint: ws://127.0.0.1:8765/ws

============================================================
  Setup Complete!
============================================================

Next steps:
  • Run 'smolclaw tui' to start the interactive assistant
  • Run 'smolclaw gateway status' to check gateway status
  • Edit config at: ~/.smolclaw/config/config.json
```

### Verbose Output
```
  Configuration:
    provider: huggingface
    model: Qwen/Qwen2.5-7B-Instruct
    base_url: https://router.huggingface.co/v1
    api_key: ********
    hf_token: ********
    headless: False
    gateway_host: 127.0.0.1
    gateway_port: 8765
```

## Post-Setup Commands

### Check Configuration
```bash
cat ~/.smolclaw/config/config.json
```

### Check Gateway Status
```bash
smolclaw gateway status
```

### Start TUI
```bash
smolclaw tui
```

### Test Connection
```bash
# If gateway is running
smolclaw tui --ensure-gateway
```

## Troubleshooting

### Hugging Face Login Fails
```bash
# Make sure token is valid
smolclaw setup --hf-token NEW_TOKEN
```

### Gateway Won't Start
```bash
# Check if port is in use
lsof -i :8765

# Use different port
smolclaw setup --hf-token YOUR_TOKEN --gateway-port 9000
```

### Permission Denied
```bash
# On macOS/Linux, may need to fix permissions
chmod -R 755 ~/.smolclaw
```

### Model Not Found
```bash
# Try different model
smolclaw setup --hf-token YOUR_TOKEN --model Qwen/Qwen2.5-7B-Instruct
```

## Migration from Old Setup

If you used the old `smolclaw onboard` command:

```bash
# Old way (still works)
smolclaw onboard

# New way (recommended)
smolclaw setup --hf-token YOUR_TOKEN
```

The new `setup` command does everything `onboard` did, plus:
- Creates directory structure
- Configures gateway
- Can start gateway automatically
- More options for customization

## Environment Variables

Alternatively, you can set these environment variables:

```bash
export HF_TOKEN=your_token
export SMOLCLAW_MODEL=Qwen/Qwen2.5-7B-Instruct
export SMOLCLAW_BASE_URL=https://router.huggingface.co/v1

# Then run setup without arguments
smolclaw setup
```

## Configuration File Location

- **macOS/Linux:** `~/.smolclaw/config/config.json`
- **Windows:** `C:\Users\You\.smolclaw\config\config.json`

## Default Values

| Setting | Default |
|---------|---------|
| Provider | `huggingface` |
| Model | `Qwen/Qwen2.5-7B-Instruct` |
| Base URL | `https://router.huggingface.co/v1` |
| Gateway Host | `127.0.0.1` |
| Gateway Port | `8765` |
| Headless | `False` |
| Start Gateway | `True` |

## Help

```bash
# Show help
smolclaw setup --help

# Show version
smolclaw --version
```
