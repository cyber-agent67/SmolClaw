# agentic_navigator vs smolclaw - What's the Difference?

## Quick Answer

| Package | Purpose | Analogy |
|---------|---------|---------|
| **agentic_navigator** | Core AI Agent engine | The "engine" - provides the core navigation logic |
| **smolclaw** | Runtime wrapper + CLI | The "car" - wraps the engine with controls, UI, and features |

---

## agentic_navigator (Core Engine)

**Location:** `agentic_navigator/`

**Purpose:** Core AI Agent navigation logic using Entity-Interaction Model (EIM)

**What it contains:**
```
agentic_navigator/
├── main.py                    # Core agent orchestration
│   └── run_agent_with_args()  # Main entry point
│
├── entities/                  # State containers
│   ├── browser/               # Browser, Tab, NavigationStack
│   └── memory/                # ExperienceMemory
│
├── interactions/              # Business logic
│   ├── agent/                 # Initialize, Run, Cleanup
│   ├── browser/               # Initialize browser
│   ├── navigation/            # GoToURL, GoBack
│   ├── tab/                   # Create, Switch, Close
│   └── tools/                 # All AI Agent tools
│       ├── ToolRegistry.py    # Main tool registry
│       ├── vision/            # Florence-2 tool
│       ├── exploration/       # A* tool
│       └── q_learning/        # Q-learning tool
│
├── repositories/              # Persistence
│   ├── ExperienceRepository.py
│   └── PromptCacheRepository.py
│
└── config/                    # Configuration
    └── BrowserConfig.py
```

**Key Functions:**
- `run_agent_with_args(args)` - Run the AI agent with parsed arguments
- `cleanup_resources()` - Clean up browser resources

**Usage:**
```python
from agentic_navigator.main import run_agent_with_args

result = run_agent_with_args(args)
```

---

## smolclaw (Runtime Wrapper)

**Location:** `smolclaw/`

**Purpose:** Runtime wrapper that adds CLI, gateway, TUI, and smolhand support

**What it contains:**
```
smolclaw/
├── agentic_runner.py          # Bridge to agentic_navigator
│   └── run_agent_with_args()  # Wraps agentic_navigator + adds tool prompts
│
├── loop.py                    # Run orchestrator
│   ├── execute_run_loop()     # Single execution
│   └── await_commands_loop()  # Persistent mode
│
├── tool_calling.py            # smolhand runtime
│   ├── OpenAICompatClient
│   ├── SmolhandRunner
│   └── default_tools
│
├── cli.py                     # CLI commands
│   ├── smolclaw tui
│   ├── smolclaw gateway
│   └── smolclaw onboard
│
├── gateway/                   # Websocket gateway
│   └── tui_client.py
│
├── config.py                  # smolclaw-specific config
└── templates/                 # Prompt templates
    ├── prompts/
    └── skills/
```

**Key Functions:**
- `run_agent_with_args(args)` - Enhanced version with tool prompts
- `cleanup_resources()` - Cleanup wrapper
- `OpenAICompatClient` - For smolhand (small LLM) runtime
- `SmolhandRunner` - Tool-calling runner for small models

**Usage:**
```python
from smolclaw import run_agent_with_args, OpenAICompatClient, SmolhandRunner

# Use full agent (smolclaw runtime)
result = run_agent_with_args(args)

# Use small LLM (smolhand runtime)
llm = OpenAICompatClient(model="Qwen/Qwen2.5-7B-Instruct")
runner = SmolhandRunner(llm_client=llm)
result = runner.run(prompt, max_loops=4)
```

---

## Relationship

```
┌─────────────────────────────────────────────────────────────┐
│                        smolclaw                              │
│                   (Runtime Wrapper)                          │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │   CLI (tui)    │  │    Gateway     │  │   smolhand    │ │
│  │                │  │  (websocket)   │  │   (small LLM) │ │
│  └───────┬────────┘  └───────┬────────┘  └───────┬───────┘ │
│          │                   │                    │         │
│          └───────────────────┼────────────────────┘         │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │   loop.py         │                    │
│                    │   (orchestrator)  │                    │
│                    └─────────┬─────────┘                    │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │  agentic_runner   │                    │
│                    │  (bridge)         │                    │
│                    └─────────┬─────────┘                    │
└──────────────────────────────┼──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    agentic_navigator                         │
│                     (Core Engine)                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  main.py: run_agent_with_args()                        │ │
│  └────────────────────────────────────────────────────────┘ │
│          │                                                   │
│          ▼                                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tools: vision, exploration, q_learning, browser       │ │
│  └────────────────────────────────────────────────────────┘ │
│          │                                                   │
│          ▼                                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Entities + Interactions (EIM architecture)            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Differences

| Aspect | agentic_navigator | smolclaw |
|--------|-------------------|----------|
| **Purpose** | Core AI Agent logic | Runtime wrapper + features |
| **Dependencies** | None (core) | Depends on agentic_navigator |
| **Runtimes** | One (full agent) | Two (smolclaw + smolhand) |
| **CLI** | No | Yes (tui, gateway, onboard) |
| **Gateway** | No | Yes (websocket server) |
| **Templates** | No | Yes (prompts, skills) |
| **Small LLM** | No | Yes (smolhand runtime) |
| **Loop Mode** | No | Yes (await commands) |

---

## When to Use Which

### Use agentic_navigator when:
- You want the core AI agent logic only
- You're building a custom runtime
- You don't need CLI or gateway features
- You want minimal dependencies

```python
from agentic_navigator.main import run_agent_with_args

result = run_agent_with_args(args)
```

### Use smolclaw when:
- You want the full-featured runtime
- You need CLI (tui, gateway)
- You want smolhand (small LLM) support
- You want loop mode (await commands)
- You want prompt templates

```python
# CLI
smolclaw tui

# Or programmatically
from smolclaw import run_agent_with_args

result = run_agent_with_args(args)

# Or smolhand (small LLM)
from smolclaw import OpenAICompatClient, SmolhandRunner

llm = OpenAICompatClient(model="Qwen/Qwen2.5-7B-Instruct")
runner = SmolhandRunner(llm_client=llm)
result = runner.run(prompt, max_loops=4)
```

---

## File Import Paths

### agentic_navigator (Core)
```python
# Core agent
from agentic_navigator.main import run_agent_with_args

# Tools
from agentic_navigator.tools.ToolRegistry import ToolRegistry
from agentic_navigator.tools.vision import analyze_visual_context
from agentic_navigator.tools.exploration import explore_dom_with_astar
from agentic_navigator.tools.q_learning import score_task_progress_q_learning

# Entities
from agentic_navigator.entities.browser.Browser import Browser
from agentic_navigator.entities.browser.Tab import Tab

# Interactions
from agentic_navigator.interactions.agent.Run import RunAgent
from agentic_navigator.interactions.navigation.GoToURL import GoToURL
```

### smolclaw (Runtime)
```python
# Main runtime
from smolclaw import run_agent_with_args, cleanup_resources

# smolhand (small LLM)
from smolclaw import OpenAICompatClient, SmolhandRunner, default_tools

# Loop mode
from smolclaw.loop import execute_run_loop, await_commands_loop

# Gateway
from smolclaw.gateway.tui_client import run_tui_sync
```

---

## Summary

**agentic_navigator** = The core AI Agent engine
- Pure EIM architecture
- Core navigation logic
- All intelligence tools

**smolclaw** = The full-featured runtime
- Wraps agentic_navigator
- Adds CLI (tui, gateway)
- Adds smolhand (small LLM)
- Adds loop mode
- Adds templates

**You typically use smolclaw** because it provides the complete runtime experience. Use agentic_navigator only if you're building a custom runtime or want minimal dependencies.
