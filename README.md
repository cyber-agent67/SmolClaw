# SMOL claw

SMOL claw is a stripped-down autonomous web navigator refactored into an Entity-Interaction Model (EIM) architecture.

## Quick Start

```bash
# 1. Install
uv pip install -e .

# 2. Setup (one command)
smolclaw setup --hf-token YOUR_HF_TOKEN

# 3. Run
smolclaw tui
```

That's it! You're ready to go. 🎉

## Architecture

The codebase follows a clean separation:

- **smolclaw/agent/**: AI Agent core (THE BRAIN)
  - Tools: Vision, Exploration, Q-Learning
  - Entities: Browser, Tab, NavigationStack
  - Interactions: Business logic
  
- **smolclaw/tools/**: Tool integrations
  - **smolhand**: Browser automation + Small LLM (THE HANDS)
  - **smoleyes**: Vision analysis with Florence-2 (THE EYES)
  
- **smolclaw/gateway/**: Gateway and API
  - WebSocket server for agent access
  - REST API for Chronicle SSPM
  - TUI client
  
- **smolclaw/**: Runtime wrapper (THE BODY)
  - CLI: tui, gateway, setup
  - Loop: Run orchestrator

Backward compatibility is preserved:

- `navigate.py` continues to work without CLI changes
- Root `main.py` is the single entrypoint and delegates to `smolclaw.loop.main()`
- The run loop is implemented inside `smolclaw/loop.py` and can stay alive awaiting commands

## Setup

### One-Command Setup (Recommended)

```bash
# Quick setup with defaults
smolclaw setup --hf-token YOUR_HF_TOKEN

# Full setup with all options
smolclaw setup \
    --hf-token YOUR_TOKEN \
    --model Qwen/Qwen2.5-7B-Instruct \
    --headless \
    --start-gateway

# See all options
smolclaw setup --help
```

This creates `~/.smolclaw/` with:
- `config/config.json` - Your configuration
- `workplace/` - Working directory
- `mcp/` - MCP add-ons
- `SOUL.md`, `TOOLS.md`, `SKILLS.md` - Agent templates

### Manual Setup

**Linux/macOS**

1. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

2. Install editable package:

```bash
uv pip install -e .
```

3. Run onboarding:

```bash
smolclaw onboard
```

**Windows (PowerShell)**

1. Create and activate a virtual environment:

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
```

2. Install editable package:

```powershell
uv pip install -e .
```

3. Run onboarding:

```powershell
smolclaw onboard
```

### Notes

- `uv` is the primary environment/package manager for this project.
- Primary install path: `uv pip install -e .`.
- `requirements.txt` remains available as a pinned dependency snapshot when needed.
- CI validates install on both Linux and Windows via `.github/workflows/install-matrix.yml`.

**Recommended:** Use `smolclaw setup --hf-token YOUR_TOKEN` for one-command setup.

SmolClaw auto-creates a home workspace at `~/.smolclaw` with:

- `config/` for runtime config, pid, and logs
- `SOUL.md`, `TOOLS.md` (plus compatibility `TOOS.md`), and `SKILLS.md` seeded from packaged templates
- `workplace/` as the default local working area for agent artifacts
- `mcp/` for MCP add-ons and integrations

## Run

Recommended (personal assistant mode):

```bash
smolclaw tui
```

This opens an interactive CLI where you type tasks and the agent executes them.

You can still run direct script commands when needed:

```bash
python navigate.py --url "https://www.google.com" --prompt "Find the latest release"
```

Or use:

```bash
python main.py --url "https://www.google.com" --prompt "Find the latest release"
```

Run with explicit top-level loop controls:

```bash
python main.py --runtime smolhand --prompt "Summarize current page" --max-loops 6 --iterations 2 --continue-on-error
```

Run in persistent await-command mode (stdin):

```bash
python main.py --runtime smolhand --await-commands --command-source stdin
```

Run in persistent await-command mode (gateway queue file):

```bash
python main.py --runtime smolhand --await-commands --command-source gateway_queue --command-queue-file data/gateway_commands.queue
```

Type `exit` (or `quit`) to stop loop mode.

## smolhand Tool Calling (Small LLM)

This repository now includes `smolhand`, a lightweight tool-calling runtime for small models.

What it does:

- JSON-first tool calling (`{"tool_call": {"name": ..., "arguments": ...}}`)
- ReAct fallback parsing (`Action:` and `Action Input:`)
- Backend tool execution loop with result injection
- Declarative page-session connection via `ensure_connected_page(url)` for one-page workflows

Run with a Hugging Face OpenAI-compatible endpoint:

```bash
python navigate.py \
	--runtime smolhand \
	--prompt "Summarize the current page" \
	--smolhand-model "Qwen/Qwen2.5-7B-Instruct" \
	--smolhand-base-url "https://router.huggingface.co/v1" \
	--smolhand-api-key "$HF_TOKEN"
```

Default `smolhand` tools in this repo:

- Browser/navigation tools from the shared tool registry when those dependencies are available
- Declarative page-session lifecycle tools: `connect_to_page(url, headless=False)` and `close_page_session()`
- Automatic tab fallback for page-reading tools when the current page is dead or inaccessible
- General-purpose fallback tools (`fetch_url(url)`, `get_time()`, `echo(text)`) when the browser registry cannot load

When running `--runtime smolhand`, the loop now auto-connects to `--url` before executing the prompt so a single page can be treated as the primary task context.

Default runtime remains `smolclaw` for browser navigation.

The `smolclaw onboard` command now performs Hugging Face login as part of setup and stores a Hugging Face-only model configuration for the gateway/runtime.

Gateway expansion plan:

- `smolclaw.gateway` is the current websocket gateway server.
- `smolclaw/loop.py` includes pluggable command sources: `stdin`, `gateway_queue`, and a reserved `telegram` source.
- Telegram is not implemented yet, but the loop now has a dedicated integration hook for adding it in the gateway layer.

## smolclaw Package Layout

The main agentic runner is available in `smolclaw/agentic_runner.py`.

Related package-level surfaces are also exposed under `smolclaw/`:

- `smolclaw.entities` re-exports the core entity types
- `smolclaw.interactions` re-exports the interaction layer, including smolhand-related actions
- `smolclaw.tools` re-exports the tool registry and smolhand tool adapter
- `smolclaw.tool_calling` re-exports the `smolhand` tool-calling runtime

## Templates Policy

Prompts and skills should be stored as markdown templates under `smolclaw/templates/`.

- Prompt templates: `smolclaw/templates/prompts/*.md`
- Skill templates: `smolclaw/templates/skills/**/*.md`

Runtime code should load templates via `smolclaw/templates_loader.py` instead of hardcoding prompt text in Python source.

## browser_subagents Package

The root `browser_subagents/` package is now the browser sub-agent surface:

- `browser_subagents.exploration` includes a `HeuristicExplorer` with `q_learning` and `a_star` style scoring
- `browser_subagents.navigation` wraps navigation and scouting interactions
- `browser_subagents.extraction` wraps page/DOM extraction interactions
- `browser_subagents.tools` exposes tool-calling runtime access (`SmolhandRunner`, `ToolRegistry`)

### Layered Browser Service Model

The browser tooling now follows layered services:

1. Layer 1 (`browser_subagents/layers/layer1_browser/`):
	- Raw browser/page/DOM access (`url`, `title`, `page_source`, link extraction)
2. Layer 2 (`browser_subagents/layers/layer2_florence_vision/`):
	- Screenshot capture + Florence bridge that returns visual context tied to the main prompt
3. Layer 3 (`browser_subagents/layers/layer3_dom_explorer/`):
	- A* hyperlink exploration over DOM/href heuristics to rank candidate paths
4. Layer 4 (`browser_subagents/layers/layer4_q_learning/`):
	- Q-learning style task progress scoring where reward combines task/page vector similarity and optional LLM score

Each layer now follows a consistent Entity-Interaction folder layout:

- `entities.py`: layer-specific state payloads
- `interactions.py`: layer-specific logic/actions
- `__init__.py`: layer exports

Service facades are centralized under `browser_subagents/services/` and are what the tool registry imports.

These layers are exposed as tools in `ToolRegistry`:
- `analyze_visual_context(prompt_hint)`
- `explore_dom_with_astar(target, keyword_values, top_k)`
- `score_task_progress_q_learning(task_prompt, llm_score, action_name)`

For scout navigation, the main agent can pass valuable keyword weights to `find_path_to_target(..., keyword_values=...)`.
The optional `"__strategy"` key supports selecting the scoring mode, for example:

```json
{
	"__strategy": "q_learning",
	"release": 18,
	"changelog": 10,
	"version": 8
}
```