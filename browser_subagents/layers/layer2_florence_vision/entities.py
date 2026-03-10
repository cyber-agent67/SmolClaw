"""Entities for Layer 2 (screenshot + Florence bridge)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class VisionContextEntity:
    prompt_hint: str
    url: str
    title: str
    florence_status: str
    visual_caption: str
    visual_detail: str
    regions: List[Dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "prompt_hint": self.prompt_hint,
            "url": self.url,
            "title": self.title,
            "florence_status": self.florence_status,
            "visual_caption": self.visual_caption,
            "visual_detail": self.visual_detail,
            "regions": self.regions,
        }
