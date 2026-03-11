"""Service facade for Layer 3 (A* DOM exploration).

Note: This is a stub for compatibility. A* exploration is in smolclaw.agent.tools.exploration.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


class DOMExplorerLayerService:
    """Service facade for Layer 3 DOM exploration."""

    @staticmethod
    def explore(
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Explore current page with A* heuristics."""
        return {
            "target": target,
            "strategy": "a_star",
            "note": "Use smolclaw.agent.tools.exploration for full A* exploration",
            "ranked_links": [],
        }

    @staticmethod
    def explore_json(
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        top_k: int = 5,
    ) -> str:
        """Explore and return JSON."""
        return json.dumps(
            DOMExplorerLayerService.explore(target, keyword_weights, top_k),
            indent=2,
        )


__all__ = ["DOMExplorerLayerService"]
