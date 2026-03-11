# Corrected Architecture: Q-Learning is an AI Agent Tool

## Correction Summary

**Q-learning is NOT a browser layer.** It is an **AI Agent tool** located in `agentic_navigator/tools/q_learning/`.

---

## Correct Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SMOLCLAW SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         AI AGENT                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    TOOL REGISTRY                                │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │  │  │
│  │  │  │ Browser Tools│  │ Scout Tools  │  │ Q-Learning Tool    │   │  │  │
│  │  │  │              │  │              │  │                    │   │  │  │
│  │  │  │ - get_DOM    │  │ - find_path  │  │ - score_task_      │   │  │  │
│  │  │  │ - snapshot   │  │ _to_target   │  │   progress_q_      │   │  │  │
│  │  │  │ - navigate   │  │              │  │   learning         │   │  │  │
│  │  │  │ - tabs       │  │              │  │                    │   │  │  │
│  │  │  └──────────────┘  └──────────────┘  └────────────────────┘   │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    │ Tool Calls                             │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    BROWSER SUBAGENTS (3 Layers)                       │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  LAYER 1: Raw Browser Access                                   │  │  │
│  │  │  browser_subagents/layers/layer1_browser/                      │  │  │
│  │  │  - page_state.py (entities)                                    │  │  │
│  │  │  - page_operations.py (interactions)                           │  │  │
│  │  │  Service: BrowserLayerService                                  │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                                    ▲                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  LAYER 2: Florence Vision                                      │  │  │
│  │  │  browser_subagents/layers/layer2_florence_vision/              │  │  │
│  │  │  - vision_context.py (entities)                                │  │  │
│  │  │  - vision_analysis.py (interactions)                           │  │  │
│  │  │  Service: FlorenceVisionLayerService                           │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                                    ▲                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │  LAYER 3: A* DOM Exploration                                   │  │  │
│  │  │  browser_subagents/layers/layer3_dom_explorer/                 │  │  │
│  │  │  - exploration_results.py (entities)                           │  │  │
│  │  │  - dom_exploration.py (interactions)                           │  │  │
│  │  │  Service: DOMExplorerLayerService                              │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Distinction

### Browser Subagents (3 Layers)
**Purpose:** Provide browser automation capabilities

| Layer | Purpose | Location |
|-------|---------|----------|
| 1 | Raw browser access | `browser_subagents/layers/layer1_browser/` |
| 2 | Florence-2 vision | `browser_subagents/layers/layer2_florence_vision/` |
| 3 | A* DOM exploration | `browser_subagents/layers/layer3_dom_explorer/` |

### AI Agent Tools
**Purpose:** Provide decision-making capabilities to the agent

| Tool | Purpose | Location |
|------|---------|----------|
| Browser Tools | Navigate, extract, interact | `agentic_navigator/tools/ToolRegistry.py` |
| Scout Tools | Find paths, explore | `agentic_navigator/interactions/scout/` |
| **Q-Learning Tool** | **Score navigation progress** | **`agentic_navigator/tools/q_learning/`** |

---

## Q-Learning Tool Location

```
agentic_navigator/tools/q_learning/
├── __init__.py              # Package exports
├── entities.py              # QLearningScoreEntity, QLearningState
├── interactions.py          # ScoreTaskProgress (computation logic)
└── tool.py                  # score_task_progress_q_learning (@tool decorated)
```

### Usage in ToolRegistry

```python
# agentic_navigator/tools/ToolRegistry.py

@tool
def score_task_progress_q_learning(task_prompt: str, llm_score: float = None, action_name: str = "observe") -> str:
    """AI Agent tool: computes task/page vector reward and updates Q-value for navigation learning."""
    from agentic_navigator.tools.q_learning import score_task_progress_q_learning as q_tool
    
    recovery_note = _recover_live_page("score_task_progress_q_learning")
    payload = q_tool(task_prompt, llm_score=llm_score, action_name=action_name)
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload
```

---

## Why Q-Learning is NOT a Browser Layer

1. **State Management**: Q-learning maintains a state table (`q_values`, `visit_counts`) that persists across browser operations
2. **Decision Support**: It provides scoring for the AI Agent's navigation decisions, not browser operations
3. **Tool Interface**: It's exposed as a `@tool` decorated function for the agent to call
4. **Separation of Concerns**: Browser layers handle browser operations; Q-learning handles navigation learning

---

## Corrected File Structure

```
agentic_navigator/
├── tools/
│   ├── ToolRegistry.py          # Main tool registry with all @tool functions
│   └── q_learning/              # Q-learning tool package
│       ├── __init__.py
│       ├── entities.py          # QLearningScoreEntity, QLearningState
│       ├── interactions.py      # ScoreTaskProgress computation
│       └── tool.py              # score_task_progress_q_learning @tool

browser_subagents/
├── layers/
│   ├── layer1_browser/          # Raw browser access
│   ├── layer2_florence_vision/  # Vision analysis
│   └── layer3_dom_explorer/     # A* exploration
├── services/
│   ├── layer1_browser.py        # BrowserLayerService
│   ├── layer2_florence_vision.py # FlorenceVisionLayerService
│   └── layer3_dom_explorer.py   # DOMExplorerLayerService
└── scoring/
    └── heuristic_scorer.py      # HeuristicScorer (shared by L3 and scout)
```

---

## Summary

- ✅ **Browser Subagents** = 3 layers (browser operations)
- ✅ **Q-Learning** = AI Agent tool (navigation scoring)
- ✅ **Location** = `agentic_navigator/tools/q_learning/`
- ✅ **Interface** = `@tool` decorated function `score_task_progress_q_learning`

This separation ensures:
- Clear boundaries between browser operations and agent decision-making
- Q-learning state persists independently of browser state
- Tools can be composed flexibly by the AI Agent
