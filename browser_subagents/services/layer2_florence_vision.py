"""Service facade for Layer 2 (screenshot + Florence bridge)."""

from __future__ import annotations

import json
from typing import Any, Dict

from browser_subagents.layers.layer2_florence_vision.interactions import BuildVisionContext


class FlorenceVisionLayerService:
	@staticmethod
	def describe_current_view(prompt_hint: str = "") -> Dict[str, Any]:
		context = BuildVisionContext.execute(prompt_hint)
		return context.as_dict()

	@staticmethod
	def describe_current_view_json(prompt_hint: str = "") -> str:
		return json.dumps(FlorenceVisionLayerService.describe_current_view(prompt_hint), indent=2)
__all__ = ["FlorenceVisionLayerService"]
