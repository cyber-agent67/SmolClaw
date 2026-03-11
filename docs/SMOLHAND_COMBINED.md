# ✅ SmolHand: Combined Browser + Small LLM Runtime

## What Changed

**browser_subagents** and **smolhand** have been **combined** into a single package: **smolclaw.smolhand**

## New Structure

```
smolclaw/
├── smolhand/                    ← NEW! Combined package
│   ├── __init__.py              # Main exports
│   ├── runtime.py               # Small LLM tool-calling runtime
│   │
│   ├── layers/
│   │   └── layer1_browser/      # Raw browser access
│   │       ├── page_state.py
│   │       └── page_operations.py
│   │
│   ├── scoring/
│   │   └── heuristic_scorer.py  # A* exploration utility
│   │
│   └── services/
│       └── layer1_browser.py    # BrowserLayerService facade
│
├── agent/                       # AI Agent Core
│   └── tools/                   # Intelligence tools
│       ├── vision/
│       ├── exploration/         ← Uses smolhand.scoring
│       └── q_learning/
│
└── tool_calling.py              # Re-exports smolhand runtime
```

## What's Inside smolclaw.smolhand

### 1. Browser Automation (Layer 1)
```python
from smolclaw.smolhand import BrowserLayerService

# Get page state
state = BrowserLayerService.current_page_state()
# → {"url": "...", "title": "...", "page_source": "..."}

# Extract links
links = BrowserLayerService.extract_links()
# → [{"href": "...", "text": "...", "title": "..."}]

# Get DOM tree
dom = BrowserLayerService.dom_tree_json()
# → JSON string
```

### 2. Heuristic Scoring (Shared Utility)
```python
from smolclaw.smolhand import HeuristicScorer

scorer = HeuristicScorer(strategy="a_star")
ranked = scorer.rank_links(
    links=links,
    current_url=url,
    target="release notes",
    top_k=5,
)
# → Ranked links with scores
```

### 3. Small LLM Runtime
```python
from smolclaw.smolhand import OpenAICompatClient, SmolhandRunner

# Initialize client
llm = OpenAICompatClient(
    model="Qwen/Qwen2.5-7B-Instruct",
    base_url="https://router.huggingface.co/v1",
    api_key="your-key"
)

# Initialize runner
runner = SmolhandRunner(llm_client=llm)

# Connect to page
ensure_connected_page("https://example.com")

# Run with tools
result = runner.run("Summarize this page", max_loops=4)
```

## Import Paths

### Old (browser_subagents)
```python
# OLD - Don't use
from browser_subagents.services import BrowserLayerService
from browser_subagents.scoring import HeuristicScorer
```

### Old (smolhand)
```python
# OLD - Don't use
from smolhand import OpenAICompatClient, SmolhandRunner
```

### New (smolclaw.smolhand)
```python
# NEW - Use these
from smolclaw.smolhand import BrowserLayerService
from smolclaw.smolhand import HeuristicScorer
from smolclaw.smolhand import OpenAICompatClient, SmolhandRunner
from smolclaw.smolhand import ensure_connected_page, close_page_session
```

### Or via smolclaw.tool_calling (backward compatible)
```python
from smolclaw.tool_calling import OpenAICompatClient, SmolhandRunner
```

## Usage Examples

### Example 1: Browser Automation Only
```python
from smolclaw.smolhand import BrowserLayerService

# Get current page info
state = BrowserLayerService.current_page_state()
print(f"Currently on: {state['url']}")

# Extract all links
links = BrowserLayerService.extract_links()
print(f"Found {len(links)} links")
```

### Example 2: Small LLM Tool-Calling
```python
from smolclaw.smolhand import OpenAICompatClient, SmolhandRunner, ensure_connected_page

# Setup
llm = OpenAICompatClient(model="Qwen/Qwen2.5-7B-Instruct")
runner = SmolhandRunner(llm_client=llm)

# Connect to page
result = ensure_connected_page("https://example.com")

# Run agent
response = runner.run("What is this page about?", max_loops=4)
print(response)
```

### Example 3: A* Link Exploration
```python
from smolclaw.smolhand import HeuristicScorer, BrowserLayerService

# Get links from current page
links = BrowserLayerService.extract_links()

# Score links for finding "release notes"
scorer = HeuristicScorer(strategy="a_star")
ranked = scorer.rank_links(
    links=links,
    current_url="https://example.com",
    target="release notes",
    keyword_weights={"release": 18, "version": 8},
    top_k=5,
)

print(f"Best link: {ranked[0]['href']}")
```

## Files Updated

All imports have been updated in:
- ✅ `smolclaw/agent/` (all tools and interactions)
- ✅ `smolclaw/__init__.py` (exports smolhand)
- ✅ `browser/browser_wrapper.py`
- ✅ `smolclaw/tool_calling.py` (re-exports for backward compatibility)

## Old Directories

- ❌ `browser_subagents/` - **DELETED**
- ❌ `smolhand/` - **DELETED**
- ✅ `smolclaw/smolhand/` - **NEW** (combined package)

## Benefits

1. **Single Package**: Browser automation + small LLM runtime in one place
2. **Clearer Naming**: "smolhand" suggests "small hand" for browser control
3. **Tighter Integration**: Runtime and browser automation are closely coupled
4. **Simpler Imports**: One package name for all browser/LLM operations

## Summary

| Old | New |
|-----|-----|
| `browser_subagents/` | `smolclaw/smolhand/layers/` |
| `smolhand/` | `smolclaw/smolhand/runtime.py` |
| `from browser_subagents import ...` | `from smolclaw.smolhand import ...` |
| `from smolhand import ...` | `from smolclaw.smolhand import ...` |

**smolclaw.smolhand** is now your **one-stop package** for browser automation and small LLM tool-calling! 🤖👐
