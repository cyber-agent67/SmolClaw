"""Service facade for Layer 2 (screenshot + Florence bridge).

Note: This is a stub for compatibility. Florence-2 integration requires the vision model.
"""

from __future__ import annotations

import json
from typing import Any, Dict


class FlorenceVisionLayerService:
    """Service facade for Layer 2 vision operations."""

    @staticmethod
    def describe_current_view(prompt_hint: str = "") -> Dict[str, Any]:
        """Describe the current page view."""
        return {
            "prompt_hint": prompt_hint,
            "florence_status": "not-configured",
            "note": "Florence-2 vision model not configured",
        }

    @staticmethod
    def describe_current_view_json(prompt_hint: str = "") -> str:
        """Describe the current page view as JSON."""
        return json.dumps(
            FlorenceVisionLayerService.describe_current_view(prompt_hint),
            indent=2,
        )


__all__ = ["FlorenceVisionLayerService"]
