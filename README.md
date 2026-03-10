# SMOL claw

SMOL claw is a stripped-down autonomous web navigator refactored into an Entity-Interaction Model (EIM) architecture.

## Architecture

The codebase now follows an EIM split:

- `agentic_navigator/entities`: pure state containers
- `agentic_navigator/interactions`: pure logic and side-effect operations
- `agentic_navigator/repositories`: persistence access
- `agentic_navigator/tools`: smolagents `@tool` wrappers only
- `agentic_navigator/config`: runtime configuration entities
- `agentic_navigator/main.py`: orchestrator for `run_agent_with_args`

Backward compatibility is preserved:

- `agent.py` is a shim that exports `run_agent_with_args` and `cleanup_resources`
- `navigate.py` continues to work without CLI changes
- Root `main.py` delegates to `navigate.main()`

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run `smolclaw onboard` and complete the Hugging Face login flow. For now, onboarding is restricted to Hugging Face models only.

## Run

```bash
python navigate.py --url "https://www.google.com" --prompt "Find the latest release"
```

Or use:

```bash
python main.py --url "https://www.google.com" --prompt "Find the latest release"
```

## smolhand Tool Calling (Small LLM)

This repository now includes `smolhand`, a lightweight tool-calling runtime for small models.

What it does:

- JSON-first tool calling (`{"tool_call": {"name": ..., "arguments": ...}}`)
- ReAct fallback parsing (`Action:` and `Action Input:`)
- Backend tool execution loop with result injection

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
- Automatic tab fallback for page-reading tools when the current page is dead or inaccessible
- General-purpose fallback tools (`fetch_url(url)`, `get_time()`, `echo(text)`) when the browser registry cannot load

Default runtime remains `smolclaw` for browser navigation.

The `smolclaw onboard` command now performs Hugging Face login as part of setup and stores a Hugging Face-only model configuration for the gateway/runtime.