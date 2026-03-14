# SmolClaw Final Architecture

## Core Principle: Separation of Concerns

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI AGENT                                 │
│                  (agentic_navigator)                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    TOOL REGISTRY                            │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │ │
│  │  │  VISION      │  │ EXPLORATION  │  │   Q-LEARNING     │ │ │
│  │  │  TOOL        │  │ TOOL         │  │   TOOL           │ │ │
│  │  │              │  │              │  │                  │ │ │
│  │  │  Florence-2  │  │  A* Heuristic│  │   Navigation     │ │ │
│  │  │  Analysis    │  │  Link Ranking│  │   Scoring        │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │ │
│  │  │   SCOUT      │  │   BROWSER    │  │   NAVIGATION     │ │ │
│  │  │   TOOL       │  │   TOOLS      │  │   TOOLS          │ │ │
│  │  │              │  │              │  │                  │ │ │
│  │  │  Depth-1     │  │  DOM, Tabs,  │  │  GoToURL,        │ │ │
│  │  │  Lookahead   │  │  Snapshot    │  │  GoBack, Tabs    │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Tool Calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER SUBAGENTS                             │
│                 (browser_subagents)                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              LAYER 1: RAW BROWSER ACCESS                    │ │
│  │                                                             │ │
│  │  browser_subagents/layers/layer1_browser/                  │ │
│  │  ├── page_state.py          (entities)                     │ │
│  │  └── page_operations.py     (interactions)                 │ │
│  │                                                             │ │
│  │  BrowserLayerService:                                       │ │
│  │  - current_page_state()    (URL, title, page_source)       │ │
│  │  - extract_links()         (hyperlinks)                    │ │
│  │  - dom_tree_json()         (DOM structure)                 │ │
│  │  - page_snapshot_json()    (complete snapshot)             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           SHARED: Heuristic Scorer                          │ │
│  │                                                             │ │
│  │  browser_subagents/scoring/heuristic_scorer.py             │ │
│  │  - HeuristicScorer                                          │ │
│  │  - Used by: Exploration Tool, Scout Tool                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Package Structure

### agentic_navigator/ (AI Agent)

```
agentic_navigator/
├── tools/                      # ← ALL INTELLIGENCE LIVES HERE
│   ├── ToolRegistry.py         # Main tool registry
│   │
│   ├── vision/                 # Vision Tool (Florence-2)
│   │   ├── __init__.py
│   │   ├── entities.py         # VisionContextEntity
│   │   ├── interactions.py     # BuildVisionContext
│   │   └── tool.py             # analyze_visual_context (@tool)
│   │
│   ├── exploration/            # Exploration Tool (A*)
│   │   ├── __init__.py
│   │   ├── entities.py         # RankedLinkEntity, ExplorationResultEntity
│   │   ├── interactions.py     # ExploreCurrentPageAStar
│   │   └── tool.py             # explore_dom_with_astar (@tool)
│   │
│   └── q_learning/             # Q-Learning Tool
│       ├── __init__.py
│       ├── entities.py         # QLearningScoreEntity, QLearningState
│       ├── interactions.py     # ScoreTaskProgress
│       └── tool.py             # score_task_progress_q_learning (@tool)
│
├── entities/                   # Agent entities (Browser, Tab, NavigationStack)
├── interactions/               # Agent interactions (navigation, tabs, etc.)
├── repositories/               # Persistence (cache, experience, navigation stack)
└── main.py                     # Agent orchestration
```

### browser_subagents/ (Dumb Browser)

```
browser_subagents/
├── layers/
│   └── layer1_browser/         # ONLY Layer 1 (raw browser access)
│       ├── __init__.py
│       ├── page_state.py       # PageStateEntity, LinkEntity, BrowserSnapshotEntity
│       └── page_operations.py  # ReadCurrentPage, ExtractHyperlinks, BuildBrowserSnapshot
│
├── services/
│   └── layer1_browser.py       # BrowserLayerService facade
│
├── scoring/
│   └── heuristic_scorer.py     # HeuristicScorer (shared by tools)
│
├── config.py                   # Layer 1 configuration only
├── exceptions.py               # Browser-related exceptions
├── metrics.py                  # Browser operation metrics
└── main.py                     # Browser subagent entry point
```

---

## Tool Catalog

### Vision Tool (Florence-2)
**Location:** `agentic_navigator/tools/vision/tool.py`

```python
@tool
def analyze_visual_context(prompt_hint: str = "") -> str:
    """Use Florence-2 vision AI to analyze the current page's visual content.
    
    Returns: JSON with visual_caption, visual_detail, regions
    """
```

### Exploration Tool (A*)
**Location:** `agentic_navigator/tools/exploration/tool.py`

```python
@tool
def explore_dom_with_astar(target: str, keyword_values: str = None, top_k: int = 5) -> str:
    """Use A* heuristics to rank hyperlinks on the current page by relevance.
    
    Returns: JSON with ranked_links (href, text, title, score)
    """
```

### Q-Learning Tool
**Location:** `agentic_navigator/tools/q_learning/tool.py`

```python
@tool
def score_task_progress_q_learning(task_prompt: str, llm_score: float = None, action_name: str = "observe") -> str:
    """Compute task/page vector reward and update Q-value for navigation learning.
    
    Returns: JSON with state, action, vector_reward, q_value, visits
    """
```

### Scout Tool (FindPathToTarget)
**Location:** `agentic_navigator/interactions/scout/FindPathToTarget.py`

```python
class FindPathToTarget:
    @staticmethod
    def execute(target: str, keyword_values: Optional[str] = None) -> ScoutResult:
        """Depth-1 lookahead: opens top links, scores content, returns best URL."""
```

### Browser Tools
**Location:** `agentic_navigator/tools/ToolRegistry.py`

```python
@tool
def get_DOM_Tree() -> str: ...

@tool
def get_browser_snapshot() -> str: ...

@tool
def set_browser_url(url: str) -> str: ...

@tool
def create_new_tab(url: str = None) -> str: ...

@tool
def switch_to_tab(tab_id: str) -> str: ...

@tool
def close_tab(tab_id: str) -> str: ...

@tool
def list_open_tabs() -> str: ...

@tool
def go_back() -> str: ...

@tool
def quit_browser() -> str: ...
```

---

## Key Design Decisions

### 1. Browser is Dumb
- **browser_subagents** only provides Layer 1 (raw browser access)
- No intelligence, no decision-making
- Just exposes browser state and basic operations

### 2. All Intelligence in Tools
- **Vision**, **Exploration**, and **Q-Learning** are AI Agent tools
- Each tool has its own entities, interactions, and @tool interface
- Tools can be composed flexibly by the agent

### 3. Shared Scoring Logic
- **HeuristicScorer** lives in browser_subagents/scoring/
- Used by both Exploration Tool and Scout Tool
- Keeps scoring logic DRY (Don't Repeat Yourself)

### 4. Clear Boundaries
```
┌──────────────────────┬──────────────────────────────────────┐
│  browser_subagents   │  agentic_navigator                   │
│  (Dumb Browser)      │  (Smart Agent)                       │
├──────────────────────┼──────────────────────────────────────┤
│  - Layer 1 only      │  - All tools                         │
│  - BrowserLayerService│  - Vision Tool                      │
│  - HeuristicScorer   │  - Exploration Tool                  │
│  - Config/Exceptions │  - Q-Learning Tool                   │
│  - Metrics           │  - Scout Tool                        │
│                      │  - Browser Tools (navigation, tabs)  │
└──────────────────────┴──────────────────────────────────────┘
```

---

## Usage Example

```python
# AI Agent decides which tools to use based on task

# Task: "Find the latest release notes"
agent.decide()
  → explore_dom_with_astar("release notes", keyword_values={"release": 18})
  → Returns: ranked links with scores

# Task: "What buttons are visible on this page?"
agent.decide()
  → analyze_visual_context("Find all buttons")
  → Returns: visual analysis with button locations

# Task: "Navigate to the best page for release info"
agent.decide()
  → score_task_progress_q_learning("find release notes", action_name="click_link")
  → Returns: Q-value update for learning
```

---

## File Count Summary

### agentic_navigator/tools/
- `vision/` - 4 files (entities, interactions, tool, __init__)
- `exploration/` - 4 files (entities, interactions, tool, __init__)
- `q_learning/` - 4 files (entities, interactions, tool, __init__)
- `ToolRegistry.py` - 1 file

**Total: 13 files for all intelligence**

### browser_subagents/
- `layers/layer1_browser/` - 3 files (page_state, page_operations, __init__)
- `services/` - 1 file (layer1_browser.py)
- `scoring/` - 1 file (heuristic_scorer.py)
- Config, exceptions, metrics, main - 4 files

**Total: 9 files for dumb browser**

---

## Benefits

1. **Clear Separation**: Browser operations vs Agent intelligence
2. **Modular Tools**: Each intelligence layer is independent
3. **Flexible Composition**: Agent can use any combination of tools
4. **Testable**: Tools can be tested independently
5. **Maintainable**: Changes to one tool don't affect others
6. **Scalable**: Easy to add new tools without modifying browser code

---

## Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| **Browser** | `browser_subagents/` | Dumb browser automation (Layer 1 only) |
| **Vision Tool** | `agentic_navigator/tools/vision/` | Florence-2 visual analysis |
| **Exploration Tool** | `agentic_navigator/tools/exploration/` | A* link ranking |
| **Q-Learning Tool** | `agentic_navigator/tools/q_learning/` | Navigation scoring |
| **Scout Tool** | `agentic_navigator/interactions/scout/` | Depth-1 lookahead |
| **Browser Tools** | `agentic_navigator/tools/ToolRegistry.py` | Navigation, tabs, DOM |

**This is the correct architecture!** 🎉
