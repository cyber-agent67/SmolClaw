"""SmolHand: Browser automation + Small LLM runtime.

This package combines:
1. Browser automation (Layer 1 raw browser access)
2. Heuristic scoring (A* exploration utility)
3. Small LLM tool-calling runtime

Structure:
- layers/layer1_browser/: Raw browser access
- scoring/: HeuristicScorer utility
- runtime.py: Small LLM tool-calling runtime
"""

from smolclaw.tools.smolhand.layers.layer1_browser.page_operations import (
    BuildBrowserSnapshot,
    ExtractHyperlinks,
    ReadCurrentPage,
)
from smolclaw.tools.smolhand.layers.layer1_browser.page_state import (
    BrowserSnapshotEntity,
    LinkEntity,
    PageStateEntity,
)
from smolclaw.tools.smolhand.runtime import (
    OpenAICompatClient,
    SmolhandRunner,
    ToolDefinition,
    close_page_session,
    default_tools,
    ensure_connected_page,
)
from smolclaw.tools.smolhand.scoring import HeuristicScorer
from smolclaw.tools.smolhand.services import BrowserLayerService

__all__ = [
    # Browser Layer 1
    "PageStateEntity",
    "LinkEntity",
    "BrowserSnapshotEntity",
    "ReadCurrentPage",
    "ExtractHyperlinks",
    "BuildBrowserSnapshot",
    "BrowserLayerService",
    # Scoring
    "HeuristicScorer",
    # Runtime
    "OpenAICompatClient",
    "SmolhandRunner",
    "ToolDefinition",
    "ensure_connected_page",
    "close_page_session",
    "default_tools",
]
