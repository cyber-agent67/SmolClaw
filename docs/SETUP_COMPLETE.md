# ✅ One-Command Setup Complete!

## What Was Created

A comprehensive `smolclaw setup` command that configures everything through CLI arguments.

## Usage

### Quick Setup (Most Common)
```bash
smolclaw setup --hf-token YOUR_HF_TOKEN
```

### Full Setup (All Options)
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

### Help
```bash
smolclaw setup --help
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--provider` | `huggingface` | LLM provider |
| `--model` | `Qwen/Qwen2.5-7B-Instruct` | Model name |
| `--base-url` | `https://router.huggingface.co/v1` | API base URL |
| `--api-key` | (empty) | API key |
| `--hf-token` | (empty) | Hugging Face token |
| `--headless` | `False` | Headless browser |
| `--gateway-host` | `127.0.0.1` | Gateway host |
| `--gateway-port` | `8765` | Gateway port |
| `--start-gateway` | `True` | Start gateway |
| `--verbose`, `-v` | `False` | Verbose output |

## What It Does

### Step-by-Step Output

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

## Files Modified

1. **smolclaw/cli.py**
   - Added `setup` command with all options
   - Updated help text
   - Imported constants from config

2. **smolclaw/config.py**
   - Added `HUGGINGFACE_BASE_URL` constant
   - Added `HUGGINGFACE_MODELS` list
   - Exported constants for CLI use

3. **README.md**
   - Added Quick Start section
   - Updated Setup section with one-command setup
   - Updated architecture diagram

## Examples

### Example 1: Minimal Setup
```bash
smolclaw setup --hf-token hf_abc123
```

### Example 2: Headless Server
```bash
smolclaw setup \
    --hf-token hf_abc123 \
    --headless \
    --no-start-gateway
```

### Example 3: Custom Port
```bash
smolclaw setup \
    --hf-token hf_abc123 \
    --gateway-port 9000 \
    --start-gateway
```

### Example 4: Verbose Output
```bash
smolclaw setup \
    --hf-token hf_abc123 \
    --verbose
```

## Comparison: Old vs New

### Old Way (Still Works)
```bash
# Interactive prompts
smolclaw onboard

# Then manually start gateway
smolclaw gateway start

# Then run TUI
smolclaw tui
```

### New Way (Recommended)
```bash
# One command does everything
smolclaw setup --hf-token YOUR_TOKEN --start-gateway

# Then run TUI
smolclaw tui
```

## Benefits

1. **Single Command**: Everything in one place
2. **Scriptable**: Perfect for CI/CD and automation
3. **Clear Output**: Step-by-step progress
4. **Flexible**: All options configurable
5. **Verbose Mode**: Debug when needed
6. **Gateway Integration**: Can start gateway automatically

## Migration

If you used `smolclaw onboard` before:

```bash
# Old command (still works)
smolclaw onboard

# New command (recommended)
smolclaw setup --hf-token YOUR_TOKEN
```

The new `setup` command:
- Does everything `onboard` did
- Plus creates directory structure
- Plus configures gateway
- Plus can start gateway automatically
- Plus has more options

## Testing

```bash
# Test setup command
smolclaw setup --help

# Test with fake token (should warn but complete)
smolclaw setup --hf-token test_token --verbose

# Test full flow
smolclaw setup --hf-token YOUR_TOKEN --start-gateway
smolclaw gateway status
smolclaw tui
```

## Documentation

- `docs/SETUP_COMMAND.md` - Full setup command documentation
- `README.md` - Updated with quick start
- `docs/FINAL_STRUCTURE.md` - Complete architecture

## Summary

✅ **One command sets up everything:**
- Directory structure (`~/.smolclaw/`)
- Configuration (`config.json`)
- Hugging Face authentication
- Gateway settings
- Optional gateway startup

✅ **Clear, step-by-step output**

✅ **Flexible options for all use cases**

✅ **Backward compatible** - `smolclaw onboard` still works!

**Setup is now as simple as:**
```bash
smolclaw setup --hf-token YOUR_TOKEN
smolclaw tui
```

🎉
