"""Vision tool entities for AI Agent visual analysis.

This module provides state containers for Florence-2 vision analysis.
The vision tool is used by the AI Agent to understand page visual content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class VisionContextEntity:
    """Represents visual context from Florence-2 analysis of the current page.

    Attributes:
        prompt_hint: Optional hint that guided the visual analysis
        url: Current page URL
        title: Current page title
        florence_status: Model loading status
        visual_caption: Brief visual description
        visual_detail: Detailed visual description
        regions: List of detected regions with descriptions
    """
    prompt_hint: str
    url: str
    title: str
    florence_status: str
    visual_caption: str
    visual_detail: str
    regions: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "prompt_hint": self.prompt_hint,
            "url": self.url,
            "title": self.title,
            "florence_status": self.florence_status,
            "visual_caption": self.visual_caption,
            "visual_detail": self.visual_detail,
            "regions": self.regions,
        }


__all__ = ["VisionContextEntity"]
