# File Renaming and Optimization Recommendations

## Overview

This document provides specific recommendations for renaming files and optimizing the SmolClaw codebase based on the Entity-Interaction Model (EIM) architecture and layered browser services.

---

## Priority 1: Critical Optimizations

### 1.1 Consolidate Browser Wrapper Duplication

**Problem:** `browser/browser_wrapper.py` duplicates functionality now provided by the layered service architecture.

**Current State:**
```
browser/
└── browser_wrapper.py    # 450+ lines duplicating Layer 1-3 functionality
```

**Recommended Action:** Refactor to use layer services

```python
# browser/browser_wrapper.py (REFACTORED)
from browser_subagents.services import (
    BrowserLayerService,
    DOMExplorerLayerService,
    FlorenceVisionLayerService,
)

class BrowserWrapper:
    """Thin wrapper over layer services for backward compatibility."""

    async def observe_page(self) -> dict:
        # Delegate to Layer 1 service
        snapshot = BrowserLayerService.page_snapshot_json()
        return json.loads(snapshot)

    async def extract_hyperlinks(self) -> list[dict]:
        # Delegate to Layer 1 service
        return BrowserLayerService.extract_links()

    async def explore_links_astar(
        self,
        target: str,
        keyword_weights: dict[str, float] | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        # Delegate to Layer 3 service
        return DOMExplorerLayerService.explore(target, keyword_weights, top_k)["ranked_links"]
```

**Benefit:** Reduces code duplication, centralizes logic, easier maintenance.

---

### 1.2 Rename Generic Entity/Interaction Files

**Problem:** Files named `entities.py` and `interactions.py` are not descriptive when viewed in isolation.

**Current Structure:**
```
browser_subagents/layers/layer1_browser/
├── entities.py          # ❌ Generic name
└── interactions.py      # ❌ Generic name
```

**Recommended Renames:**

```
browser_subagents/layers/layer1_browser/
├── __init__.py
├── page_state.py        # ✓ Renamed from entities.py
└── page_operations.py   # ✓ Renamed from interactions.py

browser_subagents/layers/layer2_florence_vision/
├── __init__.py
├── vision_context.py    # ✓ Renamed from entities.py
└── vision_analysis.py   # ✓ Renamed from interactions.py

browser_subagents/layers/layer3_dom_explorer/
├── __init__.py
├── exploration_results.py  # ✓ Renamed from entities.py
└── dom_exploration.py      # ✓ Renamed from interactions.py

browser_subagents/layers/layer4_q_learning/
├── __init__.py
├── q_learning_scores.py # ✓ Renamed from entities.py
└── task_scoring.py      # ✓ Renamed from interactions.py
```

**Implementation:**

```bash
# Layer 1
mv browser_subagents/layers/layer1_browser/entities.py \
   browser_subagents/layers/layer1_browser/page_state.py
mv browser_subagents/layers/layer1_browser/interactions.py \
   browser_subagents/layers/layer1_browser/page_operations.py

# Layer 2
mv browser_subagents/layers/layer2_florence_vision/entities.py \
   browser_subagents/layers/layer2_florence_vision/vision_context.py
mv browser_subagents/layers/layer2_florence_vision/interactions.py \
   browser_subagents/layers/layer2_florence_vision/vision_analysis.py

# Layer 3
mv browser_subagents/layers/layer3_dom_explorer/entities.py \
   browser_subagents/layers/layer3_dom_explorer/exploration_results.py
mv browser_subagents/layers/layer3_dom_explorer/interactions.py \
   browser_subagents/layers/layer3_dom_explorer/dom_exploration.py

# Layer 4
mv browser_subagents/layers/layer4_q_learning/entities.py \
   browser_subagents/layers/layer4_q_learning/q_learning_scores.py
mv browser_subagents/layers/layer4_q_learning/interactions.py \
   browser_subagents/layers/layer4_q_learning/task_scoring.py
```

**Update Imports:**

```python
# browser_subagents/layers/layer1_browser/__init__.py (BEFORE)
from browser_subagents.layers.layer1_browser.entities import (
    BrowserSnapshotEntity,
    LinkEntity,
    PageStateEntity,
)
from browser_subagents.layers.layer1_browser.interactions import (
    BuildBrowserSnapshot,
    ExtractHyperlinks,
    ReadCurrentPage,
)

# browser_subagents/layers/layer1_browser/__init__.py (AFTER)
from browser_subagents.layers.layer1_browser.page_state import (
    BrowserSnapshotEntity,
    LinkEntity,
    PageStateEntity,
)
from browser_subagents.layers.layer1_browser.page_operations import (
    BuildBrowserSnapshot,
    ExtractHyperlinks,
    ReadCurrentPage,
)
```

---

### 1.3 Centralize Heuristic Scoring

**Problem:** `HeuristicExplorer` is used by multiple layers but lives in `exploration/`.

**Current:**
```
browser_subagents/
├── exploration/
│   └── HeuristicExplorer.py  # Used by L3 and L4
```

**Recommended:**
```
browser_subagents/
├── scoring/
│   ├── __init__.py
│   └── heuristic_scorer.py   # Renamed from HeuristicExplorer.py
```

**Implementation:**

```bash
mkdir -p browser_subagents/scoring
mv browser_subagents/exploration/HeuristicExplorer.py \
   browser_subagents/scoring/heuristic_scorer.py
```

**Update Class Name:**

```python
# browser_subagents/scoring/heuristic_scorer.py (RENAME CLASS)
# BEFORE: class HeuristicExplorer
# AFTER:
class HeuristicScorer:
    """Ranks links and pages using weighted keyword signals and strategy-specific heuristics."""
    # ... existing implementation ...
```

**Update All Imports:**

```python
# Find and replace in all files:
# FROM: from browser_subagents.exploration.HeuristicExplorer import HeuristicExplorer
# TO:   from browser_subagents.scoring.heuristic_scorer import HeuristicScorer

# Files to update:
# - browser_subagents/services/layer3_dom_explorer.py
# - browser_subagents/layers/layer3_dom_explorer/interactions.py
# - browser/browser_wrapper.py
# - agentic_navigator/tools/ToolRegistry.py (if imported)
```

---

## Priority 2: Add Type Safety

### 2.1 Complete Type Hints in Service Facades

**Current:**
```python
# browser_subagents/services/layer3_dom_explorer.py
class DOMExplorerLayerService:
    @staticmethod
    def explore(target, keyword_weights=None, top_k=5):
        ...
```

**Recommended:**
```python
# browser_subagents/services/layer3_dom_explorer.py
from __future__ import annotations
from typing import Any, Dict, Optional

class DOMExplorerLayerService:
    @staticmethod
    def explore(
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Explore current page with A* heuristics.

        Args:
            target: Target description for link ranking
            keyword_weights: Optional keyword weights for scoring
            top_k: Number of top links to return

        Returns:
            Dictionary with ranked links and exploration metadata
        """
        result = ExploreCurrentPageAStar.execute(
            target,
            keyword_weights=keyword_weights,
            top_k=top_k,
        )
        return result.as_dict()
```

**Files to Update:**
- [ ] `browser_subagents/services/layer1_browser.py`
- [ ] `browser_subagents/services/layer2_florence_vision.py`
- [ ] `browser_subagents/services/layer3_dom_explorer.py`
- [ ] `browser_subagents/services/layer4_q_learning.py`

---

### 2.2 Add Return Types to Interactions

**Current:**
```python
# browser_subagents/layers/layer1_browser/interactions.py
class ReadCurrentPage:
    @staticmethod
    def execute() -> PageStateEntity:
        ...
```

**Recommended (add explicit imports):**
```python
# browser_subagents/layers/layer1_browser/page_operations.py
from __future__ import annotations
from typing import List

from browser_subagents.layers.layer1_browser.page_state import (
    BrowserSnapshotEntity,
    LinkEntity,
    PageStateEntity,
)

class ReadCurrentPage:
    @staticmethod
    def execute() -> PageStateEntity:
        ...

class ExtractHyperlinks:
    @staticmethod
    def execute() -> List[LinkEntity]:
        ...

class BuildBrowserSnapshot:
    @staticmethod
    def execute() -> BrowserSnapshotEntity:
        ...
```

---

## Priority 3: Error Handling

### 3.1 Create Exception Hierarchy

**New File:** `browser_subagents/exceptions.py`

```python
"""Exception hierarchy for browser subagents."""

from __future__ import annotations


class BrowserSubAgentError(Exception):
    """Base exception for all browser subagent errors."""


# Layer 1 Exceptions
class BrowserLayerError(BrowserSubAgentError):
    """Error in Layer 1 (raw browser access) operations."""


class PageNotLoadedError(BrowserLayerError):
    """Raised when page content is not available."""


class BrowserDriverError(BrowserLayerError):
    """Raised when browser driver is not initialized or fails."""


# Layer 2 Exceptions
class VisionLayerError(BrowserSubAgentError):
    """Error in Layer 2 (vision) operations."""


class FlorenceModelError(VisionLayerError):
    """Raised when Florence model fails to load or process."""


class ScreenshotError(VisionLayerError):
    """Raised when screenshot capture fails."""


# Layer 3 Exceptions
class ExplorationLayerError(BrowserSubAgentError):
    """Error in Layer 3 (DOM exploration) operations."""


class ExplorationError(ExplorationLayerError):
    """Raised when A* exploration fails."""


class LinkExtractionError(ExplorationLayerError):
    """Raised when hyperlink extraction fails."""


# Layer 4 Exceptions
class QLearningLayerError(BrowserSubAgentError):
    """Error in Layer 4 (Q-learning) operations."""


class QValueError(QLearningLayerError):
    """Raised when Q-value computation fails."""


class TaskScoringError(QLearningLayerError):
    """Raised when task scoring fails."""


# General Exceptions
class TabNotFoundError(BrowserSubAgentError):
    """Raised when a tab cannot be found or switched to."""


class NavigationError(BrowserSubAgentError):
    """Raised when navigation fails."""
```

**Update Services to Use Exceptions:**

```python
# browser_subagents/services/layer1_browser.py (BEFORE)
class BrowserLayerService:
    @staticmethod
    def current_page_state() -> Dict[str, Any]:
        try:
            page = ReadCurrentPage.execute()
            return {...}
        except Exception as exc:
            return {"error": str(exc)}

# browser_subagents/services/layer1_browser.py (AFTER)
from browser_subagents.exceptions import BrowserDriverError, PageNotLoadedError

class BrowserLayerService:
    @staticmethod
    def current_page_state() -> Dict[str, Any]:
        try:
            page = ReadCurrentPage.execute()
            if not page.page_source:
                raise PageNotLoadedError("Current page source is empty")
            return {...}
        except (BrowserDriverError, PageNotLoadedError):
            raise
        except Exception as exc:
            raise BrowserDriverError(f"Failed to read current page: {exc}") from exc
```

---

## Priority 4: Configuration

### 4.1 Add Per-Layer Configuration

**New File:** `browser_subagents/config.py`

```python
"""Configuration for browser subagents layers."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Layer1Config:
    """Configuration for Layer 1 (raw browser access)."""
    timeout_ms: int = 30000
    max_links: int = 500
    dom_settle_timeout_ms: int = 3000


@dataclass
class Layer2Config:
    """Configuration for Layer 2 (vision)."""
    florence_model_name: str = "microsoft/Florence-2-base"
    caption_max_tokens: int = 256
    detailed_caption_max_tokens: int = 512
    enable_region_detection: bool = True


@dataclass
class Layer3Config:
    """Configuration for Layer 3 (DOM exploration)."""
    default_top_k: int = 5
    scout_lookahead_tabs: int = 3
    strategy: str = "a_star"  # "a_star" or "q_learning"
    default_keyword_weights: Dict[str, float] = field(default_factory=lambda: {
        "release": 18.0,
        "changelog": 10.0,
        "version": 8.0,
        "download": 12.0,
        "docs": 6.0,
    })


@dataclass
class Layer4Config:
    """Configuration for Layer 4 (Q-learning)."""
    default_alpha: float = 0.5  # Learning rate
    default_gamma: float = 0.8  # Discount factor
    vector_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    enable_llm_scoring: bool = False
    default_llm_score: float = 0.5


@dataclass
class BrowserSubAgentsConfig:
    """Master configuration for browser subagents."""
    layer1: Layer1Config = field(default_factory=Layer1Config)
    layer2: Layer2Config = field(default_factory=Layer2Config)
    layer3: Layer3Config = field(default_factory=Layer3Config)
    layer4: Layer4Config = field(default_factory=Layer4Config)

    @classmethod
    def from_dict(cls, data: Dict) -> BrowserSubAgentsConfig:
        """Create config from dictionary."""
        return cls(
            layer1=Layer1Config(**data.get("layer1", {})),
            layer2=Layer2Config(**data.get("layer2", {})),
            layer3=Layer3Config(**data.get("layer3", {})),
            layer4=Layer4Config(**data.get("layer4", {})),
        )
```

**Update Services to Use Config:**

```python
# browser_subagents/services/layer3_dom_explorer.py
from browser_subagents.config import Layer3Config

class DOMExplorerLayerService:
    _config: Layer3Config | None = None

    @classmethod
    def configure(cls, config: Layer3Config) -> None:
        cls._config = config

    @staticmethod
    def explore(
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        top_k: int | None = None,
    ) -> Dict[str, Any]:
        config = DOMExplorerLayerService._config or Layer3Config()
        effective_top_k = top_k or config.default_top_k
        effective_weights = keyword_weights or config.default_keyword_weights

        result = ExploreCurrentPageAStar.execute(
            target,
            keyword_weights=effective_weights,
            top_k=effective_top_k,
        )
        return result.as_dict()
```

---

## Priority 5: Caching

### 5.1 Add Prompt/Result Caching

**Update:** `agentic_navigator/repositories/PromptCacheRepository.py`

```python
"""Prompt and result caching for expensive operations."""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Cached prompt/result entry."""
    key: str
    value: Any
    created_at: float
    ttl_seconds: int
    hits: int = 0

    def is_expired(self) -> bool:
        return time.time() > self.created_at + self.ttl_seconds


class PromptCacheRepository:
    """In-memory cache for expensive operations (vision, LLM scoring)."""

    def __init__(self, default_ttl_seconds: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl_seconds

    def _make_key(self, operation: str, **kwargs) -> str:
        """Create cache key from operation name and parameters."""
        key_data = json.dumps({"op": operation, "params": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, operation: str, **kwargs) -> Optional[Any]:
        """Get cached value if available and not expired."""
        key = self._make_key(operation, **kwargs)
        entry = self._cache.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._cache[key]
            return None
        entry.hits += 1
        return entry.value

    def set(
        self,
        operation: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        **kwargs
    ) -> str:
        """Cache a value with the given TTL."""
        key = self._make_key(operation, **kwargs)
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl_seconds=ttl_seconds or self._default_ttl,
        )
        return key

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        now = time.time()
        active = sum(1 for e in self._cache.values() if not e.is_expired())
        total_hits = sum(e.hits for e in self._cache.values())
        return {
            "active_entries": active,
            "total_hits": total_hits,
            "memory_entries": len(self._cache),
        }


# Global cache instance
_prompt_cache: Optional[PromptCacheRepository] = None


def get_prompt_cache() -> PromptCacheRepository:
    """Get or create the global prompt cache."""
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCacheRepository()
    return _prompt_cache
```

**Use in Layer 2 Service:**

```python
# browser_subagents/services/layer2_florence_vision.py
from agentic_navigator.repositories.PromptCacheRepository import get_prompt_cache

class FlorenceVisionLayerService:
    @staticmethod
    def describe_current_view(prompt_hint: str = "") -> Dict[str, Any]:
        cache = get_prompt_cache()

        # Try cache first
        cached = cache.get("florence_describe", prompt_hint=prompt_hint)
        if cached is not None:
            return cached

        # Cache miss - execute
        context = BuildVisionContext.execute(prompt_hint)
        result = context.as_dict()

        # Cache result for 5 minutes
        cache.set("florence_describe", result, ttl_seconds=300, prompt_hint=prompt_hint)
        return result
```

---

## Priority 6: Observability

### 6.1 Add Metrics/Logging

**New File:** `browser_subagents/metrics.py`

```python
"""Metrics and observability for browser subagents."""

from __future__ import annotations
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Collects and reports metrics."""

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        key = self._make_key(name, tags)
        self._gauges[key] = value

    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        key = self._make_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    def snapshot(self) -> Dict[str, any]:
        """Return current metrics snapshot."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "avg": sum(v) / len(v) if v else 0,
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                }
                for k, v in self._histograms.items()
            },
        }


# Global metrics collector
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


@contextmanager
def measure_latency(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Context manager to measure operation latency."""
    start = time.perf_counter()
    try:
        yield
        get_metrics().increment(f"{metric_name}.success", tags=tags)
    except Exception:
        get_metrics().increment(f"{metric_name}.error", tags=tags)
        raise
    finally:
        elapsed = time.perf_counter() - start
        get_metrics().histogram(f"{metric_name}.latency", elapsed, tags=tags)
```

**Use in Services:**

```python
# browser_subagents/services/layer1_browser.py
from browser_subagents.metrics import measure_latency, get_metrics

class BrowserLayerService:
    @staticmethod
    def current_page_state() -> Dict[str, Any]:
        with measure_latency("layer1.current_page_state"):
            page = ReadCurrentPage.execute()
            get_metrics().gauge("layer1.page_source_length", len(page.page_source))
            return {...}
```

---

## Implementation Checklist

### Phase 1: File Renaming (1-2 hours)
- [ ] Rename `entities.py` → `page_state.py` (Layer 1)
- [ ] Rename `interactions.py` → `page_operations.py` (Layer 1)
- [ ] Rename `entities.py` → `vision_context.py` (Layer 2)
- [ ] Rename `interactions.py` → `vision_analysis.py` (Layer 2)
- [ ] Rename `entities.py` → `exploration_results.py` (Layer 3)
- [ ] Rename `interactions.py` → `dom_exploration.py` (Layer 3)
- [ ] Rename `entities.py` → `q_learning_scores.py` (Layer 4)
- [ ] Rename `interactions.py` → `task_scoring.py` (Layer 4)
- [ ] Update all `__init__.py` imports

### Phase 2: Centralize Scoring (1 hour)
- [ ] Create `browser_subagents/scoring/` directory
- [ ] Move `HeuristicExplorer.py` → `scoring/heuristic_scorer.py`
- [ ] Rename class `HeuristicExplorer` → `HeuristicScorer`
- [ ] Update all imports (4-5 files)

### Phase 3: Type Safety (2-3 hours)
- [ ] Add type hints to `services/layer1_browser.py`
- [ ] Add type hints to `services/layer2_florence_vision.py`
- [ ] Add type hints to `services/layer3_dom_explorer.py`
- [ ] Add type hints to `services/layer4_q_learning.py`
- [ ] Add return types to all interaction classes

### Phase 4: Error Handling (1-2 hours)
- [ ] Create `browser_subagents/exceptions.py`
- [ ] Update Layer 1 service to use exceptions
- [ ] Update Layer 2 service to use exceptions
- [ ] Update Layer 3 service to use exceptions
- [ ] Update Layer 4 service to use exceptions

### Phase 5: Configuration (2 hours)
- [ ] Create `browser_subagents/config.py`
- [ ] Add Layer1Config, Layer2Config, Layer3Config, Layer4Config
- [ ] Update services to accept and use config
- [ ] Add config loading from environment/files

### Phase 6: Caching (1-2 hours)
- [ ] Update `PromptCacheRepository.py` with full implementation
- [ ] Add caching to Layer 2 (vision) operations
- [ ] Add caching to Layer 4 (Q-learning) scoring
- [ ] Add cache invalidation strategy

### Phase 7: Observability (1-2 hours)
- [ ] Create `browser_subagents/metrics.py`
- [ ] Add latency measurement to all layer services
- [ ] Add error counters
- [ ] Add metrics endpoint/logging

### Phase 8: Browser Wrapper Refactor (2-3 hours)
- [ ] Audit `browser/browser_wrapper.py` for duplicated logic
- [ ] Refactor to delegate to layer services
- [ ] Write tests for refactored wrapper
- [ ] Update documentation

---

## Testing Strategy

After implementing changes:

```bash
# Run existing tests to ensure no regressions
pytest browser_subagents/ -v

# Test layer services specifically
pytest browser_subagents/services/ -v

# Test scoring module
pytest browser_subagents/scoring/ -v

# Integration test
python -m browser_subagents.main --url "https://example.com" --prompt "Test navigation"
```

---

## Migration Guide

### For Developers Using Layer Services

**Before:**
```python
from browser_subagents.layers.layer1_browser.entities import PageStateEntity
from browser_subagents.exploration.HeuristicExplorer import HeuristicExplorer
```

**After:**
```python
from browser_subagents.layers.layer1_browser.page_state import PageStateEntity
from browser_subagents.scoring.heuristic_scorer import HeuristicScorer
```

### For Service Consumers

**Before:**
```python
from browser_subagents.services.layer3_dom_explorer import DOMExplorerLayerService

result = DOMExplorerLayerService.explore("release notes", top_k=5)
```

**After (with config):**
```python
from browser_subagents.services.layer3_dom_explorer import DOMExplorerLayerService
from browser_subagents.config import Layer3Config

# Optional: configure service
config = Layer3Config(default_top_k=3)
DOMExplorerLayerService.configure(config)

# Use service (now with defaults from config)
result = DOMExplorerLayerService.explore("release notes")
```

---

## Summary

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 1 | Rename entity/interaction files | 1-2h | High (clarity) |
| 1 | Centralize HeuristicExplorer | 1h | High (maintainability) |
| 2 | Add type hints | 2-3h | Medium (safety) |
| 3 | Create exception hierarchy | 1-2h | Medium (error handling) |
| 4 | Add per-layer config | 2h | Medium (flexibility) |
| 5 | Implement caching | 1-2h | Medium (performance) |
| 6 | Add observability | 1-2h | Low-Medium (debugging) |
| 8 | Refactor BrowserWrapper | 2-3h | High (reduce duplication) |

**Total Estimated Effort:** 11-17 hours

**Recommended Order:**
1. File renaming (Phase 1)
2. Centralize scoring (Phase 2)
3. Type safety (Phase 3)
4. Error handling (Phase 4)
5. Configuration (Phase 5)
6. Caching (Phase 6)
7. Observability (Phase 7)
8. BrowserWrapper refactor (Phase 8)
