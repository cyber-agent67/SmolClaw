"""Service facade for Layer 3 (A* DOM exploration)."""

from __future__ import annotations

import json
from typing import Any, Dict

from browser_subagents.layers.layer3_dom_explorer.interactions import ExploreCurrentPageAStar


class DOMExplorerLayerService:
	@staticmethod
	def explore(target: str, keyword_weights: Dict[str, float] | None = None, top_k: int = 5) -> Dict[str, Any]:
		result = ExploreCurrentPageAStar.execute(target, keyword_weights=keyword_weights, top_k=top_k)
		return result.as_dict()

	@staticmethod
	def explore_json(target: str, keyword_weights: Dict[str, float] | None = None, top_k: int = 5) -> str:
		return json.dumps(DOMExplorerLayerService.explore(target, keyword_weights=keyword_weights, top_k=top_k), indent=2)
__all__ = ["DOMExplorerLayerService"]
