# SmolClaw System Architecture

## Overview

SmolClaw is a stripped-down autonomous web navigator built on the **Entity-Interaction Model (EIM)** architecture. It provides browser automation, multi-layer navigation intelligence, and support for both large and small language models.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SMOLCLAW SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │   CLI Entry      │     │   Gateway        │     │   TUI Client     │    │
│  │   (main.py)      │     │   (websocket)    │     │   (tui_client)   │    │
│  └────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘    │
│           │                        │                        │               │
│           └────────────────────────┼────────────────────────┘               │
│                                    │                                        │
│                          ┌─────────▼─────────┐                             │
│                          │   loop.py         │                             │
│                          │   (Run Orchestrator)                            │
│                          │   - stdin source  │                             │
│                          │   - gateway queue │                             │
│                          │   - telegram (WIP)│                             │
│                          └─────────┬─────────┘                             │
│                                    │                                        │
│           ┌────────────────────────┼────────────────────────┐               │
│           │                        │                        │               │
│  ┌────────▼─────────┐   ┌─────────▼─────────┐   ┌─────────▼─────────┐     │
│  │   smolclaw       │   │   smolhand        │   │   browser_subagents│    │
│  │   Runtime        │   │   Runtime         │   │   Package          │     │
│  │   (browser agent)│   │   (tool-calling)  │   │                    │     │
│  └────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘     │
│           │                        │                        │               │
└───────────┼────────────────────────┼────────────────────────┼───────────────┘
            │                        │                        │
            ▼                        ▼                        ▼
```

---

## Core Architecture Layers

### 1. Entry Points & Orchestration

```
┌─────────────────────────────────────────────────────────────────┐
│                      ENTRY LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  main.py    │  │  navigate.py│  │  smolclaw CLI commands  │ │
│  │  (root)     │  │  (legacy)   │  │  (tui, gateway, onboard)│ │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘ │
│         │                │                       │              │
│         └────────────────┼───────────────────────┘              │
│                          │                                      │
│                 ┌────────▼────────┐                             │
│                 │  loop.py        │                             │
│                 │  (run orchestrator)                           │
│                 │  - execute_run_loop()                         │
│                 │  - await_commands_loop()                      │
│                 │  - CommandSource abstraction                  │
│                 └────────┬────────┘                             │
│                          │                                      │
│         ┌────────────────┼────────────────┐                     │
│         │                │                │                     │
│  ┌──────▼──────┐ ┌──────▼──────┐ ┌───────▼───────┐             │
│  │ smolclaw    │ │ smolhand    │ │ browser_      │             │
│  │ runtime     │ │ runtime     │ │ subagents     │             │
│  └─────────────┘ └─────────────┘ └───────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Entity-Interaction Model (EIM)

```
┌─────────────────────────────────────────────────────────────────┐
│                    EIM ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ENTITIES (Pure State Containers)                               │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  agentic_navigator/entities/                           │    │
│  │  ├── browser/                                          │    │
│  │  │   ├── Browser.py           (driver, is_running)     │    │
│  │  │   ├── Tab.py               (url, history, active)   │    │
│  │  │   └── NavigationStack.py   (stack management)       │    │
│  │  ├── memory/                                           │    │
│  │  │   └── ExperienceMemory.py  (memory storage)         │    │
│  │  ├── perception/                                       │    │
│  │  │   └── Screenshot.py        (image data)             │    │
│  │  ├── chronicle/                                        │    │
│  │  │   └── MemoryStep.py        (execution history)      │    │
│  │  └── runtime/                                          │    │
│  │      └── AgentConfig.py       (model config)           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  INTERACTIONS (Pure Logic & Side-Effects)                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  agentic_navigator/interactions/                       │    │
│  │  ├── browser/  Initialize, Quit                        │    │
│  │  ├── agent/    Initialize, Run, Cleanup                │    │
│  │  ├── navigation/ GoToURL, GoBack, SearchOnPage         │    │
│  │  ├── tab/      Create, Switch, Close                   │    │
│  │  ├── dom/      GetTree                                 │    │
│  │  ├── florence/ DescribeImage                           │    │
│  │  ├── memory/   LoadExperiences, SaveExperience         │    │
│  │  ├── screenshot/ Capture                               │    │
│  │  ├── thinking/ Think                                   │    │
│  │  ├── scout/    FindPathToTarget                        │    │
│  │  └── smolhand/ (tool-calling interactions)             │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  TOOLS (smolagents @tool wrappers)                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  agentic_navigator/tools/ToolRegistry.py               │    │
│  │  - Bridges EIM interactions to smolagents tools        │    │
│  │  - Manages tab state, navigation stack                 │    │
│  │  - Exposes layered browser services                    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layered Browser Service Model

```
┌─────────────────────────────────────────────────────────────────┐
│                  LAYERED BROWSER SERVICES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LAYER 4: Q-Learning Navigation                         │   │
│  │  browser_subagents/layers/layer4_q_learning/            │   │
│  │  - Task/page vector similarity scoring                  │   │
│  │  - Q-value updates for state-action pairs               │   │
│  │  - Reward = vector_sim + optional LLM score             │   │
│  │  Tool: score_task_progress_q_learning()                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ▲                                  │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LAYER 3: DOM Explorer (A* Heuristics)                  │   │
│  │  browser_subagents/layers/layer3_dom_explorer/          │   │
│  │  - A* hyperlink exploration                             │   │
│  │  - Keyword-weighted link scoring                        │   │
│  │  Tool: explore_dom_with_astar(target, keyword_values)   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ▲                                  │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LAYER 2: Florence Vision                               │   │
│  │  browser_subagents/layers/layer2_florence_vision/       │   │
│  │  - Screenshot capture                                   │   │
│  │  - Florence-2 visual context analysis                   │   │
│  │  Tool: analyze_visual_context(prompt_hint)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ▲                                  │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LAYER 1: Raw Browser Access                            │   │
│  │  browser_subagents/layers/layer1_browser/               │   │
│  │  - URL, title, page_source                              │   │
│  │  - DOM tree extraction                                  │   │
│  │  - Hyperlink extraction                                 │   │
│  │  Service: BrowserLayerService                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ▲                                  │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  HELIUM BROWSER DRIVER                                  │   │
│  │  (selenium-based browser automation)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                     TOOL CALL EXECUTION                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Agent Decision                                                   │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────┐                                             │
│  │ ToolRegistry    │  @tool decorated functions                  │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Layer Service   │  BrowserLayerService                        │
│  │ Facade          │  FlorenceVisionLayerService                 │
│  │                 │  DOMExplorerLayerService                    │
│  │                 │  QLearningLayerService                      │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Layer           │  entities.py (state)                        │
│  │ Implementation  │  interactions.py (logic)                    │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Helium Driver   │  Browser automation                         │
│  └─────────────────┘                                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Runtime Modes

### smolclaw Runtime (Browser Agent)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMOLCLAW RUNTIME                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────┐                                              │
│  │ Initialize    │  LoadEnv, LoadExperiences                    │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ Initialize    │  BrowserConfig → Browser (Helium driver)     │
│  │ Browser       │                                              │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ Initialize    │  LiteLLMModel / Custom model                 │
│  │ Agent         │  + screenshot callback                        │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ Run Agent     │  Main execution loop                         │
│  │ Loop          │  - Tool execution via ToolRegistry           │
│  │               │  - Memory updates                            │
│  │               │  - Navigation stack management               │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ Cleanup       │  Close browser, release resources            │
│  └───────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

### smolhand Runtime (Small LLM Tool-Calling)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMOLHAND RUNTIME                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────┐                                              │
│  │ OpenAICompat  │  HF router / Custom endpoint                 │
│  │ Client        │  - Qwen/Qwen2.5-7B-Instruct (default)        │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ SmolhandRunner│  Tool execution loop                         │
│  │               │  - JSON tool calling                         │
│  │               │  - ReAct fallback parsing                    │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ ensure_       │  Auto-connect to --url                       │
│  │ connected_page│  Creates page session context                │
│  └───────┬───────┘                                              │
│          │                                                       │
│          ▼                                                       │
│  ┌───────────────┐                                              │
│  │ default_tools │  Browser tools (fallback)                    │
│  │               │  - fetch_url()                               │
│  │               │  - get_time()                                │
│  │               │  - echo()                                    │
│  └───────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tool Registry Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      TOOL REGISTRY                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  State Management                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - _navigation_stack: NavigationStack                   │   │
│  │  - _tabs: Dict[tab_id, Tab]                             │   │
│  │  - _current_tab_id: str                                 │   │
│  │  - _tab_counter: int                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Browser Tools                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - get_DOM_Tree()                                       │   │
│  │  - get_browser_snapshot()                               │   │
│  │  - set_browser_url(url)                                 │   │
│  │  - go_back()                                            │   │
│  │  - close_popups()                                       │   │
│  │  - search_item_ctrl_f(text, nth)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Tab Management Tools                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - create_new_tab(url?)                                 │   │
│  │  - switch_to_tab(tab_id)                                │   │
│  │  - close_tab(tab_id)                                    │   │
│  │  - list_open_tabs()                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Layered Intelligence Tools                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - analyze_visual_context(prompt_hint)     [Layer 2]    │   │
│  │  - explore_dom_with_astar(target, keywords) [Layer 3]   │   │
│  │  - score_task_progress_q_learning(task, llm_score)       │   │
│  │    [Layer 4]                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Scout/Navigation Tools                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - find_path_to_target(target, keyword_values)          │   │
│  │    (depth-1 scout interaction)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Location Tools                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - get_address()        (hostname, IP, URL)             │   │
│  │  - get_geolocation()    (lat, lon, altitude, etc.)      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Cognitive Tools                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - think(query)         (strategy interaction)          │   │
│  │  - quit_browser()       (safe shutdown)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  External Tools                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - WebSearchTool()      (smolagents built-in)           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Command Sources (Long-Running Mode)

```
┌─────────────────────────────────────────────────────────────────┐
│                   COMMAND SOURCE ABSTRACTION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CommandSource (interface)                               │  │
│  │    - next_command() -> str | None                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Implementations:                                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ StdinCommand     │  │ GatewayQueue     │  │ Telegram     │ │
│  │ Source           │  │ CommandSource    │  │ CommandSource│ │
│  │                  │  │                  │  │ (reserved)   │ │
│  │ - input()        │  │ - Polls file     │  │ - Not        │ │
│  │ - Terminal CLI   │  │ - Newline delim  │  │   implemented│ │
│  │                  │  │ - Offset tracking│  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Gateway Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GATEWAY SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐         ┌─────────────┐         ┌───────────┐ │
│  │ TUI Client  │◄───────►│  Gateway    │◄───────►│ loop.py   │ │
│  │ (websocket) │  WS     │  Server     │  queue  │ (await)   │ │
│  └─────────────┘         │  (future)   │  file   └───────────┘ │
│                          └─────────────┘                       │
│                                                                  │
│  Gateway Queue File Format:                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  data/gateway_commands.queue                            │   │
│  │  - One JSON command per line                            │   │
│  │  - Polling with offset tracking                         │   │
│  │  - Non-blocking command delivery                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  TUI Client Flow:                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. Connect to gateway websocket                        │   │
│  │  2. Send: {"type": "run_prompt", "prompt": "..."}       │   │
│  │  3. Receive: {"type": "result", "result": "..."}        │   │
│  │  4. Display result, await next command                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Navigation Mission

```
┌──────────────────────────────────────────────────────────────────┐
│              NAVIGATION MISSION EXECUTION                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User Input                                                       │
│  "Find the latest release notes for version 2.0"                 │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────┐                                             │
│  │ Agent (LLM)     │  Parses intent, plans actions              │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Tool Call       │  find_path_to_target(                      │
│  │ Decision        │    "latest release notes version 2.0",     │
│  │                 │    keyword_values={"release": 18,          │
│  │                 │                     "version": 8})         │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Scout           │  Extract links from current page           │
│  │ Interaction     │  Score with keyword weights                │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Best URL        │  Navigate to highest-scored link           │
│  │ Selection       │                                              │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Q-Learning      │  Score progress, update Q-value            │
│  │ Reward Update   │  Store experience                          │
│  └────────┬────────┘                                             │
│           │                                                       │
│           ▼                                                       │
│  ┌─────────────────┐                                             │
│  │ Continue Loop   │  Next tool call or final_answer            │
│  └─────────────────┘                                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Configuration & Templates

```
┌─────────────────────────────────────────────────────────────────┐
│                 CONFIGURATION SYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Environment Variables (.env)                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - HUGGINGFACE_TOKEN                                    │   │
│  │  - Model API keys                                       │   │
│  │  - Custom endpoints                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Runtime Config (~/.smolclaw/config/)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - model: Default model name                            │   │
│  │  - base_url: API endpoint                               │   │
│  │  - api_key: Authentication token                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Templates (smolclaw/templates/)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  prompts/                                               │   │
│  │  ├── browser.md         (Browser tool prompts)          │   │
│  │  └── q_learning.md      (Q-learning tool prompts)       │   │
│  │                                                         │   │
│  │  skills/                                                │   │
│  │  └── **/*.md          (Skill templates)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Template Loading                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  templates_loader.py                                    │   │
│  │  - load_tool_prompts(tool_key) -> dict                  │   │
│  │  - Formats prompts into system instructions             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Package Structure Summary

```
smolclaw/
├── __init__.py              # Package exports (agentic_runner, tool_calling)
├── loop.py                  # Run orchestrator with command sources
├── agentic_runner.py        # Bridge to agentic_navigator.main
├── tool_calling.py          # smolhand runtime exports
├── config.py                # Config loading utilities
├── templates_loader.py      # Template loading from markdown
├── cli.py                   # CLI command definitions
├── gateway/
│   └── tui_client.py        # Websocket TUI client
└── templates/
    ├── prompts/             # Tool prompt templates
    └── skills/              # Skill templates

agentic_navigator/
├── entities/                # Pure state containers
│   ├── browser/             # Browser, Tab, NavigationStack
│   ├── memory/              # ExperienceMemory
│   ├── perception/          # Screenshot
│   └── chronicle/           # MemoryStep
├── interactions/            # Pure logic & side-effects
│   ├── browser/             # Initialize, Quit
│   ├── agent/               # Initialize, Run, Cleanup
│   ├── navigation/          # GoToURL, GoBack, SearchOnPage
│   ├── tab/                 # Create, Switch, Close
│   └── ...                  # (20+ interaction modules)
├── tools/
│   └── ToolRegistry.py      # smolagents @tool wrappers
└── repositories/            # Persistence layer
    ├── ExperienceRepository.py
    ├── NavigationStackRepository.py
    └── PromptCacheRepository.py

browser_subagents/
├── exploration/             # HeuristicExplorer (A*, Q-learning)
├── navigation/              # Navigation wrappers
├── extraction/              # Page/DOM extraction
├── services/                # Layer service facades
├── tools/                   # SmolhandRunner, ToolRegistry
└── layers/
    ├── layer1_browser/      # Raw browser access
    ├── layer2_florence_vision/  # Vision analysis
    ├── layer3_dom_explorer/ # A* link exploration
    └── layer4_q_learning/   # Q-learning scoring

browser/                     # Legacy browser module
├── browser_wrapper.py
├── bot_evasion.py
└── config.py
```

---

## Key Design Principles

1. **Entity-Interaction Model (EIM)**: Clear separation between state (entities) and behavior (interactions)
2. **Layered Intelligence**: Browser services organized in 4 layers of increasing abstraction
3. **Dual Runtime Support**: Both full browser agent (smolclaw) and lightweight tool-calling (smolhand)
4. **Pluggable Command Sources**: Support for stdin, file queues, and future Telegram integration
5. **Template-Driven Prompts**: Prompts and skills stored as markdown, loaded at runtime
6. **Backward Compatibility**: Legacy navigate.py and main.py entry points preserved
