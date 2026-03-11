# ✅ Final SmolClaw Architecture

## Complete Package Structure

```
smolclaw/
│
├── agent/                          # AI Agent Core (THE BRAIN)
│   ├── main.py                     # run_agent_with_args()
│   ├── entities/                   # State containers
│   │   ├── browser/
│   │   │   ├── Browser.py
│   │   │   ├── Tab.py
│   │   │   └── NavigationStack.py
│   │   └── memory/
│   │       └── ExperienceMemory.py
│   │
│   ├── interactions/               # Business logic (stateless)
│   │   ├── agent/                  # Initialize, Run, Cleanup
│   │   ├── browser/                # Initialize, Quit
│   │   ├── navigation/             # GoToURL, GoBack
│   │   ├── tab/                    # Create, Switch, Close
│   │   ├── scout/                  # FindPathToTarget
│   │   └── ... (more)
│   │
│   ├── tools/                      # AI Agent Intelligence
│   │   ├── ToolRegistry.py         # Main registry
│   │   ├── vision/                 # Florence-2 vision tool
│   │   ├── exploration/            # A* link ranking tool
│   │   └── q_learning/             # Q-learning scoring tool
│   │
│   ├── repositories/               # Persistence
│   │   ├── ExperienceRepository.py
│   │   ├── NavigationStackRepository.py
│   │   └── PromptCacheRepository.py
│   │
│   └── config/
│       └── BrowserConfig.py
│
├── smolhand/                       # Browser + Small LLM (THE HANDS)
│   ├── __init__.py                 # Main exports
│   ├── runtime.py                  # Small LLM tool-calling
│   │
│   ├── layers/
│   │   └── layer1_browser/         # Raw browser access
│   │       ├── page_state.py
│   │       └── page_operations.py
│   │
│   ├── scoring/
│   │   └── heuristic_scorer.py     # A* utility (shared)
│   │
│   └── services/
│       └── layer1_browser.py       # BrowserLayerService
│
├── loop.py                         # Run orchestrator
├── agentic_runner.py               # Bridge to agent
├── tool_calling.py                 # Re-exports smolhand
├── cli.py                          # CLI commands
├── gateway/                        # Websocket gateway
└── templates/                      # Prompt templates
```

## Package Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                            │
│         (CLI, Gateway, Direct Script Calls)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    smolclaw                                  │
│              (Runtime Wrapper - THE BODY)                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  loop.py     │  │  agentic_    │  │  tool_calling.py │  │
│  │  (orchestra- │  │  runner.py   │  │  (smolhand       │  │
│  │   tor)       │  │  (bridge)    │  │   re-exports)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Uses
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              smolclaw.agent       smolclaw.smolhand         │
│           (THE BRAIN)            (THE HANDS)                │
│                                                              │
│  ┌──────────────────────┐      ┌────────────────────────┐   │
│  │  AI Agent Core       │      │  Browser Automation    │   │
│  │  - Tools (Vision,    │      │  - Layer 1: Raw        │   │
│  │    Exploration,      │◄────►│    browser access      │   │
│  │    Q-Learning)       │      │  - HeuristicScorer     │   │
│  │  - Entities          │      │  - Small LLM runtime   │   │
│  │  - Interactions      │      │    (OpenAICompatClient,│   │
│  │                      │      │     SmolhandRunner)    │   │
│  └──────────────────────┘      └────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Controls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Selenium / Helium                               │
│           (Actual Browser Control)                           │
└─────────────────────────────────────────────────────────────┘
```

## The Three Packages

### 1. smolclaw.agent (AI Agent Core)

**Purpose:** Intelligence and decision-making

**Contains:**
- All AI Agent tools (Vision, Exploration, Q-Learning)
- Entity-Interaction Model (EIM) implementation
- Agent orchestration (main.py)

**Usage:**
```python
from smolclaw.agent import run_agent_with_args
from smolclaw.agent.tools.vision import analyze_visual_context
from smolclaw.agent.tools.exploration import explore_dom_with_astar
```

### 2. smolclaw.smolhand (Browser + Small LLM)

**Purpose:** Browser automation and small LLM tool-calling

**Contains:**
- Layer 1: Raw browser access (page state, links, DOM)
- HeuristicScorer: A* exploration utility
- Small LLM runtime (OpenAICompatClient, SmolhandRunner)

**Usage:**
```python
from smolclaw.smolhand import BrowserLayerService
from smolclaw.smolhand import HeuristicScorer
from smolclaw.smolhand import OpenAICompatClient, SmolhandRunner
```

### 3. smolclaw (Runtime Wrapper)

**Purpose:** Full-featured runtime with CLI, gateway, and features

**Contains:**
- loop.py: Run orchestrator
- agentic_runner.py: Bridge to agent
- tool_calling.py: Re-exports smolhand
- cli.py: CLI commands (tui, gateway, onboard)
- gateway/: Websocket server

**Usage:**
```bash
smolclaw tui  # Interactive CLI
```

```python
from smolclaw import run_agent_with_args
from smolclaw import OpenAICompatClient, SmolhandRunner
```

## Data Flow: "Find release notes"

```
User (CLI)
    ↓
smolclaw/loop.py
    ↓
smolclaw/agentic_runner.py
    ↓
smolclaw/agent/main.py
    ├─→ Initialize Browser (via smolclaw.smolhand)
    └─→ Initialize Agent (LLM with tools)
            ↓
        Agent decides:
            ↓
        explore_dom_with_astar("release notes")
            ↓
        smolclaw.agent.tools.exploration/
            ↓
        smolclaw.smolhand.scoring.HeuristicScorer
            ↓
        smolclaw.smolhand.layers.layer1_browser
            ↓
        Helium: Extract links from DOM
            ↓
        Returns ranked links
            ↓
        Agent clicks best link
            ↓
        score_task_progress_q_learning()
            ↓
        Agent learns and continues
            ↓
        final_answer("Version 2.0 released on...")
            ↓
        Result to user
```

## Import Summary

| Purpose | Import |
|---------|--------|
| Run full agent | `from smolclaw import run_agent_with_args` |
| Vision tool | `from smolclaw.agent.tools.vision import analyze_visual_context` |
| Exploration tool | `from smolclaw.agent.tools.exploration import explore_dom_with_astar` |
| Q-learning tool | `from smolclaw.agent.tools.q_learning import score_task_progress_q_learning` |
| Browser automation | `from smolclaw.smolhand import BrowserLayerService` |
| Heuristic scoring | `from smolclaw.smolhand import HeuristicScorer` |
| Small LLM runtime | `from smolclaw.smolhand import OpenAICompatClient, SmolhandRunner` |
| CLI | `smolclaw tui` |

## One-Liner Summary

```
smolclaw (body)
    ├─→ agent (brain) - AI intelligence and tools
    └─→ smolhand (hands) - Browser automation + small LLM runtime
```

**Three packages, one system:** 🧠 (agent) + 👐 (smolhand) + 🏃 (smolclaw runtime)
