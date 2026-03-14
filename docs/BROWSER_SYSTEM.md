# Browser System Architecture

## Overview

SmolClaw provides a **layered browser automation system** built on top of Selenium/Helium, with four intelligence layers that provide increasingly sophisticated navigation capabilities.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BROWSER SYSTEM STACK                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 4: Q-LEARNING NAVIGATION                                     │   │
│  │  - Task/page vector similarity scoring                              │   │
│  │  - Q-value updates for state-action pairs                           │   │
│  │  - Reward = vector_sim + optional LLM score                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 3: DOM EXPLORER (A* HEURISTICS)                              │   │
│  │  - A* hyperlink exploration                                         │   │
│  │  - Keyword-weighted link scoring                                    │   │
│  │  - Depth-1 lookahead scouting                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 2: FLORENCE VISION                                           │   │
│  │  - Screenshot capture                                               │   │
│  │  - Florence-2 visual analysis                                       │   │
│  │  - Region detection & captioning                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 1: RAW BROWSER ACCESS                                        │   │
│  │  - URL, title, page_source                                          │   │
│  │  - DOM tree extraction                                              │   │
│  │  - Hyperlink extraction                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  HELIUM / SELENIUM DRIVER                                           │   │
│  │  - Chrome WebDriver                                                 │   │
│  │  - Bot evasion (optional)                                           │   │
│  │  - Tab/window management                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Raw Browser Access

### Purpose
Provides fundamental browser automation: navigation, DOM access, and page state capture.

### File Structure
```
browser_subagents/layers/layer1_browser/
├── __init__.py
├── entities.py          # PageStateEntity, LinkEntity, BrowserSnapshotEntity
└── interactions.py      # ReadCurrentPage, ExtractHyperlinks, BuildBrowserSnapshot
```

### Entity-Interaction Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 1 ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ENTITIES (State Containers)                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PageStateEntity                                         │   │
│  │  ├── url: str                                            │   │
│  │  ├── title: str                                          │   │
│  │  └── page_source: str                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LinkEntity                                              │   │
│  │  ├── href: str                                           │   │
│  │  ├── text: str                                           │   │
│  │  └── title: str                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  BrowserSnapshotEntity                                   │   │
│  │  ├── page: PageStateEntity                               │   │
│  │  └── links: List[LinkEntity]                             │   │
│  │  └── as_dict() -> Dict                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  INTERACTIONS (Operations)                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ReadCurrentPage.execute()                               │   │
│  │    └─> PageStateEntity                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ExtractHyperlinks.execute()                             │   │
│  │    └─> List[LinkEntity]                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  BuildBrowserSnapshot.execute()                          │   │
│  │    └─> BrowserSnapshotEntity                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Service Facade

```python
# browser_subagents/services/layer1_browser.py
BrowserLayerService
├── current_page_state() -> Dict[str, Any]
├── extract_links() -> List[Dict[str, str]]
├── dom_tree_json() -> str
└── page_snapshot_json() -> str
```

### Exposed Tools
- `get_DOM_Tree()` - Full DOM tree as JSON
- `get_browser_snapshot()` - URL/title/DOM/link context
- `set_browser_url(url)` - Navigate to URL
- `go_back()` - Browser back navigation
- `close_popups()` - Close modals/popups
- `search_item_ctrl_f(text, nth)` - Find text on page

---

## Layer 2: Florence Vision

### Purpose
Integrates Florence-2 vision model for screenshot-based visual analysis of web pages.

### File Structure
```
browser_subagents/layers/layer2_florence_vision/
├── __init__.py
├── entities.py          # VisionContextEntity
└── interactions.py      # BuildVisionContext
```

### Entity-Interaction Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 2 ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ENTITY: VisionContextEntity                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  VisionContextEntity                                     │   │
│  │  ├── prompt_hint: str                                    │   │
│  │  ├── url: str                                            │   │
│  │  ├── title: str                                          │   │
│  │  ├── florence_status: str                                │   │
│  │  ├── visual_caption: str                                 │   │
│  │  ├── visual_detail: str                                  │   │
│  │  └── regions: List[Dict[str, Any]]                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  INTERACTION: BuildVisionContext                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  BuildVisionContext.execute(prompt_hint)                 │   │
│  │    │                                                      │   │
│  │    ├─> CapturePageState.execute()                        │   │
│  │    │   └─> screenshot_base64, url, title                 │   │
│  │    │                                                      │   │
│  │    ├─> LoadFlorenceModel.execute()                       │   │
│  │    │   └─> Load Florence-2 model (if available)          │   │
│  │    │                                                      │   │
│  │    └─> DescribeScreenshot.execute(screenshot_base64)     │   │
│  │        └─> caption, detailed_caption, region_descriptions│   │
│  │                                                            │   │
│  │    Returns: VisionContextEntity                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Service Facade

```python
# browser_subagents/services/layer2_florence_vision.py
FlorenceVisionLayerService
├── describe_current_view(prompt_hint="") -> Dict[str, Any]
└── describe_current_view_json(prompt_hint="") -> str
```

### Exposed Tool
- `analyze_visual_context(prompt_hint="")` - Returns Florence-2 visual analysis

### Dependencies
- Florence-2 model (optional, graceful degradation if unavailable)
- Screenshot capture from Layer 1

---

## Layer 3: DOM Explorer (A* Heuristics)

### Purpose
Ranks hyperlinks using A* heuristic scoring to find the best navigation path to a target.

### File Structure
```
browser_subagents/layers/layer3_dom_explorer/
├── __init__.py
├── entities.py          # RankedLinkEntity, ExplorationResultEntity
└── interactions.py      # ExploreCurrentPageAStar
```

### Entity-Interaction Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 3 ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ENTITIES                                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  RankedLinkEntity                                        │   │
│  │  ├── href: str                                           │   │
│  │  ├── text: str                                           │   │
│  │  ├── title: str                                          │   │
│  │  └── initial_score: float                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ExplorationResultEntity                                 │   │
│  │  ├── target: str                                         │   │
│  │  ├── strategy: str                                       │   │
│  │  ├── current_url: str                                    │   │
│  │  ├── title: str                                          │   │
│  │  └── ranked_links: List[RankedLinkEntity]                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  INTERACTION: ExploreCurrentPageAStar                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ExploreCurrentPageAStar.execute(target, keywords, top_k)│   │
│  │    │                                                      │   │
│  │    ├─> ExtractHyperlinks.execute() (Layer 1)             │   │
│  │    │   └─> List[LinkEntity]                              │   │
│  │    │                                                      │   │
│  │    ├─> HeuristicExplorer.rank_links()                    │   │
│  │    │   ├─> Signal scoring (keyword matching)             │   │
│  │    │   ├─> Strategy bonus (A* or Q-learning)             │   │
│  │    │   └─> Sort by total score                           │   │
│  │    │                                                      │   │
│  │    └─> ExplorationResultEntity                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  SCORING ALGORITHM (HeuristicExplorer)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Base Score:                                             │   │
│  │  - Exact target match: +55.0                             │   │
│  │  - Token match: +8.0 per token                           │   │
│  │  - Keyword weight match: +weight per keyword             │   │
│  │                                                            │   │
│  │  A* Strategy Bonus:                                        │   │
│  │  - Goal bonus (has target): +25.0                        │   │
│  │  - Depth penalty: -0.9 * path_depth (max -20.0)          │   │
│  │                                                            │   │
│  │  Q-Learning Strategy Bonus:                                │   │
│  │  - Exploration bonus: +6.0 (unvisited) to +2.5           │   │
│  │  - Target bonus: +18.0                                   │   │
│  │  - Revisit penalty: -6.0 per revisit                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Service Facade

```python
# browser_subagents/services/layer3_dom_explorer.py
DOMExplorerLayerService
├── explore(target, keyword_weights=None, top_k=5) -> Dict[str, Any]
└── explore_json(target, keyword_weights=None, top_k=5) -> str
```

### Exposed Tool
- `explore_dom_with_astar(target, keyword_values=None, top_k=5)` - A* link ranking

### Scout Interaction (Depth-1 Lookahead)

```
┌──────────────────────────────────────────────────────────────────┐
│                  SCOUT NAVIGATION (FIND_PATH)                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  find_path_to_target(target, keyword_values)                      │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  1. Extract links from current page                     │     │
│  │  2. Rank with A* (top 3 candidates)                     │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  For each candidate (in new tab):                       │     │
│  │    - Navigate to URL                                    │     │
│  │    - Extract page text                                  │     │
│  │    - Score content with HeuristicExplorer               │     │
│  │    - Close tab                                          │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Return best URL with confidence score                  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Layer 4: Q-Learning Navigation

### Purpose
Implements Q-learning style task progress scoring with vector similarity and optional LLM scoring.

### File Structure
```
browser_subagents/layers/layer4_q_learning/
├── __init__.py
├── entities.py          # QLearningScoreEntity
└── interactions.py      # ScoreTaskProgress
```

### Entity-Interaction Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 4 ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ENTITY: QLearningScoreEntity                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  QLearningScoreEntity                                    │   │
│  │  ├── state: str           (page URL/state identifier)    │   │
│  │  ├── action: str          (action taken)                 │   │
│  │  ├── task: str            (task prompt)                  │   │
│  │  ├── vector_reward: float (task/page similarity)         │   │
│  │  ├── llm_score: float     (optional LLM evaluation)      │   │
│  │  ├── reward: float        (combined reward)              │   │
│  │  ├── q_value: float       (updated Q-value)              │   │
│  │  ├── visits: int          (visit count)                  │   │
│  │  └── title: str           (page title)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  INTERACTION: ScoreTaskProgress                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ScoreTaskProgress.execute(                              │   │
│  │    q_values, visit_counts, task_prompt,                  │   │
│  │    action_name, llm_score, alpha, gamma                  │   │
│  │  )                                                        │   │
│  │    │                                                      │   │
│  │    ├─> Compute vector reward (task/page embedding sim)   │   │
│  │    ├─> Combine with LLM score (if provided)              │   │
│  │    ├─> Update Q-value: Q(s,a) = α * (r + γ * max Q - Q) │   │
│  │    └─> Increment visit count                             │   │
│  │                                                            │   │
│  │    Returns: QLearningScoreEntity                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Q-LEARNING FORMULA                                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Q(s,a) ← Q(s,a) + α * [r + γ * max_a' Q(s',a') - Q(s,a)]│   │
│  │                                                            │   │
│  │  Where:                                                   │   │
│  │  - α (alpha): Learning rate (default 0.5)                 │   │
│  │  - γ (gamma): Discount factor (default 0.8)               │   │
│  │  - r (reward): vector_reward + llm_score                  │   │
│  │  - s: Current state (page)                                │   │
│  │  - a: Action taken                                        │   │
│  │  - s': Next state                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Service Facade

```python
# browser_subagents/services/layer4_q_learning.py
QLearningLayerService
├── __init__()
│   ├── q_values: Dict[str, float]
│   └── visit_counts: Dict[str, int]
├── score_current_page(task_prompt, action_name, llm_score, alpha, gamma) -> Dict
└── score_current_page_json(task_prompt, action_name, llm_score, alpha, gamma) -> str
```

### Exposed Tool
- `score_task_progress_q_learning(task_prompt, llm_score=None, action_name="observe")`

---

## HeuristicExplorer: Core Scoring Engine

### Location
`browser_subagents/exploration/HeuristicExplorer.py`

### Purpose
Shared scoring engine used by both Layer 3 (A*) and Layer 4 (Q-learning).

### Class Structure

```
┌──────────────────────────────────────────────────────────────────┐
│                    HEURISTIC EXPLORER                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  HeuristicExplorer                                                │
│  ├── strategy: str ("q_learning" or "a_star")                    │
│  │                                                                │
│  ├── _normalize_weights(keyword_weights) -> Dict[str, float]     │
│  │   └─> Validates and normalizes keyword weights                │
│  │                                                                │
│  ├── _tokenize(text) -> List[str]                                │
│  │   └─> Lowercase alphanumeric tokenization                     │
│  │                                                                │
│  ├── _signal_score(text, target, keyword_weights) -> float       │
│  │   ├─> Exact target match: +55.0                               │
│  │   ├─> Token matching: +8.0 per token                          │
│  │   └─> Keyword weight matching: +weight                        │
│  │                                                                │
│  ├── _strategy_bonus(url, visit_count, has_target_token) -> float│
│  │   ├─> Q-Learning mode:                                         │
│  │   │   ├─> Exploration bonus: 6.0 - (visit_count * 1.2)        │
│  │   │   ├─> Target bonus: +18.0                                 │
│  │   │   └─> Revisit penalty: -6.0 * (visit_count - 1)           │
│  │   └─> A* mode:                                                 │
│  │       ├─> Goal bonus: +25.0                                   │
│  │       └─> Depth penalty: -0.9 * path_depth (max -20.0)        │
│  │                                                                │
│  ├── rank_links(links, current_url, target, keywords, visits, k) │
│  │   └─> Returns top-k ranked links with scores                  │
│  │                                                                │
│  └── score_page_content(page_text, title, url, target, keywords) │
│      └─> Scores full page content for scout lookahead            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Browser Wrapper (Legacy)

### Location
`browser/browser_wrapper.py`

### Purpose
Unified browser interface (custom Stagehand equivalent) that wraps Selenium/Helium with additional capabilities.

### Key Features
- Session lifecycle management (launch/close)
- Core navigation (goto, back, click, type)
- Secure credential filling
- DOM observation and page state capture
- A* hyperlink exploration (delegates to HeuristicExplorer)
- Tab management
- Vision analysis (delegates to VisionClient)

### Optimization Opportunity
This wrapper duplicates functionality now provided by the layered service architecture. Consider deprecation or refactoring to use the layer services directly.

---

## Bot Evasion

### Location
`browser/bot_evasion.py`, `browser/config.py`

### Purpose
Anti-detection arguments and JavaScript injection for browser automation.

### Configuration

```python
BOT_EVASION_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-background-timer-throttling",
    "--disable-popup-blocking",
    "--no-first-run",
    "--no-default-browser-check",
]

EVASION_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
"""
```

### Usage
Enabled via `BrowserConfig(bot_evasion=True)`.

---

## Optimization Recommendations

### 1. **Consolidate Browser Wrapper**

**Current Issue:** `browser/browser_wrapper.py` duplicates Layer 1-3 functionality.

**Recommendation:**
- Refactor `BrowserWrapper` to use layer services internally
- Or deprecate in favor of the service facade pattern

```
BEFORE:
BrowserWrapper
├── observe_page()        # Custom implementation
├── extract_hyperlinks()  # Custom implementation
└── explore_links_astar() # Duplicates HeuristicExplorer

AFTER:
BrowserWrapper
├── observe_page()        # → BrowserLayerService.page_snapshot_json()
├── extract_hyperlinks()  # → BrowserLayerService.extract_links()
└── explore_links_astar() # → DOMExplorerLayerService.explore()
```

### 2. **Rename Files for Clarity**

**Current naming is generic. Suggested renames:**

```
LAYER 1:
  entities.py           → page_state.py
  interactions.py       → page_operations.py

LAYER 2:
  entities.py           → vision_context.py
  interactions.py       → vision_analysis.py

LAYER 3:
  entities.py           → exploration_results.py
  interactions.py       → dom_exploration.py

LAYER 4:
  entities.py           → q_learning_scores.py
  interactions.py       → task_scoring.py
```

### 3. **Centralize Heuristic Scoring**

**Current:** `HeuristicExplorer` is in `browser_subagents/exploration/`

**Recommendation:** Move to a shared utilities location since it's used by multiple layers:

```
browser_subagents/
├── scoring/
│   ├── __init__.py
│   └── heuristic_scorer.py    # HeuristicExplorer moved here
```

### 4. **Add Type Hints to Service Facades**

Current service facades lack complete type annotations:

```python
# BEFORE
class DOMExplorerLayerService:
    @staticmethod
    def explore(target, keyword_weights=None, top_k=5):
        ...

# AFTER
from typing import Dict, Any, Optional

class DOMExplorerLayerService:
    @staticmethod
    def explore(
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        ...
```

### 5. **Add Caching Layer**

Add prompt/result caching for expensive operations:

```
┌──────────────────────────────────────────────────────────────────┐
│                    CACHING LAYER                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  FlorenceVisionLayerService.describe_current_view()               │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  PromptCacheRepository                                  │     │
│  │  - Cache key: (url, prompt_hint, timestamp_bucket)      │     │
│  │  - TTL: 5 minutes                                       │     │
│  │  - Return cached result if available                    │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼ (cache miss)                                              │
│  BuildVisionContext.execute()                                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 6. **Add Observability/Metrics**

```python
# Add to each layer service
class BrowserLayerService:
    @staticmethod
    def current_page_state() -> Dict[str, Any]:
        start_time = time.perf_counter()
        try:
            result = ReadCurrentPage.execute()
            metrics.record("layer1.read_page.latency", time.perf_counter() - start_time)
            metrics.increment("layer1.read_page.success")
            return result
        except Exception as e:
            metrics.increment("layer1.read_page.error")
            raise
```

### 7. **Unified Error Handling**

Create a common exception hierarchy:

```python
# browser_subagents/exceptions.py

class BrowserLayerError(Exception):
    """Base exception for browser layer operations."""

class PageNotLoadedError(BrowserLayerError):
    """Raised when page content is not available."""

class VisionModelError(BrowserLayerError):
    """Raised when Florence model fails to load."""

class ExplorationError(BrowserLayerError):
    """Raised when A*/Q-learning exploration fails."""

class QLearningError(BrowserLayerError):
    """Raised when Q-value computation fails."""
```

### 8. **Add Configuration per Layer**

```python
# browser_subagents/config.py

@dataclass
class Layer1Config:
    timeout_ms: int = 30000
    max_links: int = 500

@dataclass
class Layer2Config:
    florence_model_name: str = "microsoft/Florence-2-base"
    caption_max_tokens: int = 256

@dataclass
class Layer3Config:
    default_top_k: int = 5
    scout_lookahead_tabs: int = 3

@dataclass
class Layer4Config:
    default_alpha: float = 0.5
    default_gamma: float = 0.8
    vector_model: str = "sentence-transformers/all-MiniLM-L6-v2"
```

---

## Data Flow: Complete Navigation Mission

```
┌──────────────────────────────────────────────────────────────────┐
│              COMPLETE NAVIGATION FLOW                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User: "Find release notes for version 2.0"                      │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Agent (LLM) decides to use find_path_to_target()       │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  ToolRegistry.find_path_to_target(                      │     │
│  │    target="release notes version 2.0",                  │     │
│  │    keyword_values={"release": 18, "version": 8,         │     │
│  │                    "changelog": 10}                     │     │
│  │  )                                                        │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Scout Interaction (FindPathToTarget.execute)           │     │
│  │    │                                                     │     │
│  │    ├─> Layer 1: ExtractHyperlinks.execute()             │     │
│  │    │   └─> 47 links found                               │     │
│  │    │                                                     │     │
│  │    ├─> HeuristicExplorer.rank_links()                   │     │
│  │    │   ├─> Signal scoring with keyword weights          │     │
│  │    │   ├─> A* strategy bonus                            │     │
│  │    │   └─> Top 3: /releases (85.2), /changelog (72.1),  │     │
│  │    │       /docs (45.8)                                 │     │
│  │    │                                                     │     │
│  │    ├─> Scout Lookahead (open each in new tab)           │     │
│  │    │   ├─> /releases: content score = 92.5 ✓            │     │
│  │    │   ├─> /changelog: content score = 68.3             │     │
│  │    │   └─> /docs: content score = 41.2                  │     │
│  │    │                                                     │     │
│  │    └─> Return: {"best_url": "/releases",                │     │
│  │                 "confidence": 0.925,                    │     │
│  │                 "reason": "Content score 92.5"}         │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Agent navigates to /releases                           │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Layer 4: score_task_progress_q_learning()              │     │
│  │    ├─> Vector similarity: 0.87                          │     │
│  │    ├─> Q-value update: Q(s,a) = 0.5 * (0.87 + 0.8*0.9)  │     │
│  │    └─> Store experience                                 │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Agent uses get_DOM_Tree() to extract release info      │     │
│  └─────────────────────────────────────────────────────────┘     │
│       │                                                           │
│       ▼                                                           │
│  final_answer("Version 2.0 released on...")                      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Summary

The browser system is organized into **four intelligence layers**:

| Layer | Purpose | Key Entity | Key Interaction | Tool |
|-------|---------|------------|-----------------|------|
| L1 | Raw browser access | `PageStateEntity` | `ReadCurrentPage` | `get_DOM_Tree()` |
| L2 | Vision analysis | `VisionContextEntity` | `BuildVisionContext` | `analyze_visual_context()` |
| L3 | A* link exploration | `ExplorationResultEntity` | `ExploreCurrentPageAStar` | `explore_dom_with_astar()` |
| L4 | Q-learning scoring | `QLearningScoreEntity` | `ScoreTaskProgress` | `score_task_progress_q_learning()` |

**Key optimization opportunities:**
1. Consolidate `BrowserWrapper` to use layer services
2. Rename entity/interaction files for clarity
3. Move `HeuristicExplorer` to shared scoring module
4. Add type hints to service facades
5. Implement caching layer
6. Add observability/metrics
7. Create unified error hierarchy
8. Add per-layer configuration
