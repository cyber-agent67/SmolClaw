# SmolClaw Package Structure

## Overview

```
smolclaw/
├── agent/                     # ← AI Agent Core (formerly agentic_navigator)
│   ├── main.py                # Core agent orchestration
│   ├── entities/              # State containers
│   ├── interactions/          # Business logic
│   ├── tools/                 # AI Agent tools
│   ├── repositories/          # Persistence
│   └── config/                # Configuration
│
├── loop.py                    # Run orchestrator
├── agentic_runner.py          # Bridge to agent
├── tool_calling.py            # smolhand runtime
├── cli.py                     # CLI commands
└── gateway/                   # Websocket gateway
```

## smolclaw.agent (AI Agent Core)

**Formerly:** `agentic_navigator/`

**Purpose:** Core AI Agent navigation logic using Entity-Interaction Model (EIM)

### Structure

```
smolclaw/agent/
├── main.py                    # run_agent_with_args()
│
├── entities/
│   ├── browser/
│   │   ├── Browser.py         # Browser state
│   │   ├── Tab.py             # Tab state
│   │   └── NavigationStack.py # Navigation history
│   └── memory/
│       └── ExperienceMemory.py # Experience storage
│
├── interactions/              # Business logic (all stateless)
│   ├── agent/
│   │   ├── Initialize.py      # Initialize agent
│   │   ├── Run.py             # Run agent loop
│   │   └── Cleanup.py         # Cleanup resources
│   ├── browser/
│   │   ├── Initialize.py      # Launch browser
│   │   └── Quit.py            # Close browser
│   ├── navigation/
│   │   ├── GoToURL.py         # Navigate to URL
│   │   └── GoBack.py          # Browser back
│   ├── tab/
│   │   ├── Create.py          # Create tab
│   │   ├── Switch.py          # Switch tab
│   │   └── Close.py           # Close tab
│   └── ... (more interactions)
│
├── tools/                     # AI Agent tools (@tool decorated)
│   ├── ToolRegistry.py        # Main tool registry
│   ├── vision/
│   │   ├── tool.py            # analyze_visual_context
│   ├── exploration/
│   │   ├── tool.py            # explore_dom_with_astar
│   └── q_learning/
│       └── tool.py            # score_task_progress_q_learning
│
├── repositories/              # Persistence layer
│   ├── ExperienceRepository.py
│   ├── NavigationStackRepository.py
│   └── PromptCacheRepository.py
│
└── config/
    └── BrowserConfig.py       # Browser configuration
```

### Usage

```python
# Import from smolclaw.agent
from smolclaw.agent import run_agent_with_args, cleanup_resources

# Or import specific components
from smolclaw.agent.tools.vision import analyze_visual_context
from smolclaw.agent.tools.exploration import explore_dom_with_astar
from smolclaw.agent.tools.q_learning import score_task_progress_q_learning
```

---

## smolclaw (Runtime Wrapper)

**Purpose:** Runtime wrapper that adds CLI, gateway, TUI, and smolhand support

### Key Modules

```
smolclaw/
├── agentic_runner.py          # Bridge to smolclaw.agent
│   └── run_agent_with_args()  # Enhanced with tool prompts
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
└── gateway/
    └── tui_client.py          # Websocket TUI client
```

### Usage

```python
# Full runtime
from smolclaw import run_agent_with_args

# smolhand (small LLM)
from smolclaw import OpenAICompatClient, SmolhandRunner

# Loop mode
from smolclaw.loop import await_commands_loop
```

---

## Migration Guide

### Old Import Paths (agentic_navigator)
```python
# OLD - Don't use
from agentic_navigator.main import run_agent_with_args
from agentic_navigator.tools.vision import analyze_visual_context
```

### New Import Paths (smolclaw.agent)
```python
# NEW - Use these
from smolclaw.agent import run_agent_with_args
from smolclaw.agent.tools.vision import analyze_visual_context
from smolclaw.agent.tools.exploration import explore_dom_with_astar
from smolclaw.agent.tools.q_learning import score_task_progress_q_learning
```

---

## Summary

| Old Path | New Path |
|----------|----------|
| `agentic_navigator/` | `smolclaw/agent/` |
| `from agentic_navigator.main import ...` | `from smolclaw.agent.main import ...` |
| `from agentic_navigator.tools import ...` | `from smolclaw.agent.tools import ...` |

**All functionality remains the same - only the import path changed!**
