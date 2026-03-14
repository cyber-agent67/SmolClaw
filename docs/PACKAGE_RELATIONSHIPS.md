# SmolClaw Package Relationships

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────────────────┐  │
│  │  CLI (tui)   │      │   Gateway    │      │   Direct Script Call     │  │
│  │  smolclaw    │      │  (websocket) │      │   python main.py         │  │
│  │  tui         │      │              │      │                          │  │
│  └──────┬───────┘      └──────┬───────┘      └────────────┬─────────────┘  │
│         │                     │                            │                │
│         └─────────────────────┼────────────────────────────┘                │
│                               │                                              │
│                               ▼                                              │
│                    ┌──────────────────┐                                     │
│                    │   smolclaw/      │                                     │
│                    │   (Runtime)      │                                     │
│                    └────────┬─────────┘                                     │
│                              │                                              │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SMOLCLAW RUNTIME                                   │
│                        (smolclaw/ package)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐                                                       │
│  │  loop.py         │  ← Run orchestrator                                   │
│  │  - execute_run_loop()                                                     │
│  │  - await_commands_loop()                                                  │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │  agentic_runner  │  ← Bridge to agent                                    │
│  │  - run_agent_with_args()                                                  │
│  │  - get_agent_tools()                                                      │
│  └────────┬─────────┘                                                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                       │
│  │  tool_calling.py │  ← smolhand (small LLM)                               │
│  │  - OpenAICompatClient                                                     │
│  │  - SmolhandRunner                                                         │
│  └──────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               │ Uses
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI AGENT CORE                                        │
│                      (smolclaw/agent/)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  main.py: run_agent_with_args()                                        │ │
│  │  - Initialize browser                                                   │ │
│  │  - Initialize agent (LLM)                                               │ │
│  │  - Run agent loop                                                       │ │
│  │  - Cleanup resources                                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│           │                                                                  │
│           │ Uses                                                             │
│           ▼                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  TOOLS (AI Agent Intelligence)                                         │ │
│  │  smolclaw/agent/tools/                                                 │ │
│  │                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │ │
│  │  │  ToolRegistry.py - All available tools:                          │ │ │
│  │  │                                                                   │ │ │
│  │  │  Browser Tools:                                                   │ │ │
│  │  │  - get_DOM_Tree()              - Get full DOM                    │ │ │
│  │  │  - get_browser_snapshot()      - Page snapshot                   │ │ │
│  │  │  - set_browser_url(url)        - Navigate                        │ │ │
│  │  │  - create_new_tab()            - Create tab                      │ │ │
│  │  │  - switch_to_tab()             - Switch tab                      │ │ │
│  │  │  - close_tab()                 - Close tab                       │ │ │
│  │  │  - list_open_tabs()            - List tabs                       │ │ │
│  │  │  - go_back()                   - Browser back                    │ │ │
│  │  │  - quit_browser()              - Close browser                   │ │ │
│  │  │                                                                   │ │ │
│  │  │  Intelligence Tools:                                              │ │ │
│  │  │  - analyze_visual_context()    ← Vision Tool (Florence-2)        │ │ │
│  │  │  - explore_dom_with_astar()    ← Exploration Tool (A*)           │ │ │
│  │  │  - score_task_progress_q_learning() ← Q-Learning Tool            │ │ │
│  │  │                                                                   │ │ │
│  │  │  Scout Tools:                                                     │ │ │
│  │  │  - find_path_to_target()       ← Depth-1 lookahead               │ │ │
│  │  │                                                                   │ │ │
│  │  │  Other Tools:                                                     │ │ │
│  │  │  - get_address()               - Get URL/hostname                │ │ │
│  │  │  - get_geolocation()           - Get geo location                │ │ │
│  │  │  - search_item_ctrl_f()        - Find text on page               │ │ │
│  │  │  - close_popups()              - Close popups                    │ │ │
│  │  │  - think()                     - Cognitive strategy              │ │ │
│  │  │  - WebSearchTool()             - Web search                      │ │ │
│  │  └──────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               │ Calls
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BROWSER SUBAGENTS (Dumb Browser)                       │
│                   (browser_subagents/ package)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Layer 1: Raw Browser Access                                           │ │
│  │  browser_subagents/layers/layer1_browser/                              │ │
│  │                                                                        │ │
│  │  BrowserLayerService:                                                  │ │
│  │  - current_page_state()    → URL, title, page_source                  │ │
│  │  - extract_links()         → Hyperlinks                               │ │
│  │  - dom_tree_json()         → DOM structure                            │ │
│  │  - page_snapshot_json()    → Complete snapshot                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Shared Utility: HeuristicScorer                                       │ │
│  │  browser_subagents/scoring/heuristic_scorer.py                         │ │
│  │                                                                        │ │
│  │  - rank_links()            → Used by Exploration Tool                 │ │
│  │  - score_page_content()    → Used by Scout Tool                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
                               │ Controls
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BROWSER AUTOMATION                                    │
│                     (Selenium / Helium)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  Helium WebDriver                                                      │ │
│  │  - Navigate to URLs                                                    │ │
│  │  - Click elements                                                      │ │
│  │  - Extract DOM                                                         │ │
│  │  - Take screenshots                                                    │ │
│  │  - Manage tabs                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Package Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Dependencies                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Selenium    │  │  Helium      │  │  smolagents          │  │
│  │  (browser)   │  │  (browser)   │  │  (LLM tools)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                     │                     │
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   browser_subagents                              │
│              (Dumb browser automation)                           │
│  - Layer 1: Raw browser access                                   │
│  - HeuristicScorer: Shared scoring utility                       │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Used by
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   smolclaw.agent                                 │
│              (AI Agent Core)                                     │
│  - main.py: Agent orchestration                                  │
│  - tools/: All intelligence (Vision, A*, Q-Learning)            │
│  - entities: State containers                                    │
│  - interactions: Business logic                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Wrapped by
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   smolclaw                                       │
│              (Runtime Wrapper)                                   │
│  - loop.py: Run orchestrator                                     │
│  - agentic_runner.py: Bridge to agent                            │
│  - tool_calling.py: smolhand (small LLM)                         │
│  - cli.py: CLI commands                                          │
│  - gateway/: Websocket server                                    │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Used by
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   User Interface                                 │
│  - CLI: smolclaw tui                                             │
│  - Gateway: Websocket connections                                │
│  - Direct: Python script calls                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Example: "Find release notes"

```
User: "Find the latest release notes"
    │
    ▼
smolclaw tui (CLI)
    │
    ▼
smolclaw/loop.py: await_commands_loop()
    │
    ▼
smolclaw/agentic_runner.py: run_agent_with_args()
    │
    ▼
smolclaw/agent/main.py: run_agent_with_args()
    │
    ├─→ Initialize Browser (Helium driver)
    │
    └─→ Initialize Agent (LLM with tools)
            │
            ▼
        Agent decides to use tools:
            │
            ├─→ explore_dom_with_astar("release notes")
            │       │
            │       ├─→ smolclaw.agent.tools.exploration/
            │       │   explore_dom_with_astar()
            │       │       │
            │       │       ├─→ browser_subagents.layers.layer1_browser/
            │       │       │   ExtractHyperlinks.execute()
            │       │       │       │
            │       │       │       ▼
            │       │       │   Helium: Extract links from DOM
            │       │       │
            │       │       └─→ browser_subagents.scoring/
            │       │           HeuristicScorer.rank_links()
            │       │               │
            │       │               ▼
            │       │           Returns: Ranked links with scores
            │       │
            │       ▼
            │   Returns: JSON with top-k links
            │
            ├─→ click(link)
            │       │
            │       ▼
            │   Helium: Click on the link
            │
            ├─→ score_task_progress_q_learning("find release notes")
            │       │
            │       ├─→ smolclaw.agent.tools.q_learning/
            │       │   score_task_progress_q_learning()
            │       │       │
            │       │       ├─→ Compute vector similarity
            │       │       ├─→ Update Q-value
            │       │       │
            │       │       ▼
            │       │   Returns: Q-learning score
            │       │
            │       ▼
            │   Agent learns: "This page is relevant!"
            │
            └─→ get_DOM_Tree()
                    │
                    ├─→ smolclaw.agent.tools.ToolRegistry/
                    │   get_DOM_Tree()
                    │       │
                    │       ├─→ browser_subagents.layers.layer1_browser/
                    │       │   BrowserLayerService.dom_tree_json()
                    │       │       │
                    │       │       ▼
                    │       │   Helium: Get DOM structure
                    │       │
                    │       ▼
                    │   Returns: Full DOM tree
                    │
                    ▼
                Agent extracts release notes
                    │
                    ▼
                final_answer("Version 2.0 released on...")
                    │
                    ▼
                Result shown to user
```

---

## Key Relationships

### 1. smolclaw.agent → browser_subagents

**Relationship:** Agent uses browser as a "dumb" automation layer

```python
# smolclaw/agent/tools/exploration/tool.py
from browser_subagents.layers.layer1_browser.page_operations import (
    ExtractHyperlinks,
    ReadCurrentPage,
)
from browser_subagents.scoring.heuristic_scorer import HeuristicScorer

# Agent controls browser, browser has no intelligence
```

### 2. smolclaw → smolclaw.agent

**Relationship:** Runtime wraps agent core

```python
# smolclaw/agentic_runner.py
from smolclaw.agent.main import run_agent_with_args

# Runtime adds CLI, gateway, smolhand on top of agent
```

### 3. Tools → Interactions → Entities

**Relationship:** Tools call interactions which operate on entities

```python
# Tool (smolclaw/agent/tools/vision/tool.py)
@tool
def analyze_visual_context(prompt_hint: str = "") -> str:
    from smolclaw.agent.tools.vision.interactions import BuildVisionContext
    context = BuildVisionContext.execute(prompt_hint)
    return json.dumps(context.as_dict())

# Interaction (smolclaw/agent/tools/vision/interactions.py)
class BuildVisionContext:
    @staticmethod
    def execute(prompt_hint: str = "") -> VisionContextEntity:
        # Returns entity
        return VisionContextEntity(...)

# Entity (smolclaw/agent/tools/vision/entities.py)
@dataclass
class VisionContextEntity:
    prompt_hint: str
    url: str
    title: str
    # ... pure state container
```

### 4. HeuristicScorer (Shared Utility)

**Relationship:** Used by multiple tools (Exploration, Scout)

```python
# browser_subagents/scoring/heuristic_scorer.py
class HeuristicScorer:
    def rank_links(...) -> List[Dict]:
        # Used by Exploration Tool
        pass
    
    def score_page_content(...) -> float:
        # Used by Scout Tool
        pass

# Used by:
# - smolclaw.agent.tools.exploration/
# - smolclaw.agent.interactions.scout/
```

---

## Summary Table

| Package | Purpose | Depends On | Used By |
|---------|---------|------------|---------|
| **smolclaw** | Runtime wrapper | smolclaw.agent | User (CLI, gateway) |
| **smolclaw.agent** | AI Agent core | browser_subagents | smolclaw runtime |
| **browser_subagents** | Dumb browser | Selenium/Helium | smolclaw.agent tools |
| **browser_subagents.scoring** | Shared utility | None | Exploration, Scout tools |

---

## One-Liner Summary

```
User → smolclaw (runtime) → smolclaw.agent (AI brain) → browser_subagents (dumb hands) → Browser (actual browser)
```

**smolclaw.agent** is the **brain** that makes decisions.
**browser_subagents** is the **hands** that manipulate the browser.
**smolclaw** is the **body** that wraps everything together with CLI, gateway, and features.
