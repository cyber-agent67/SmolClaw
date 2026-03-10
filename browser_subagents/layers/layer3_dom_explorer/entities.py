"""Entities for Layer 3 (A* DOM exploration)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RankedLinkEntity:
    href: str
    text: str
    title: str
    initial_score: float


@dataclass
class ExplorationResultEntity:
    target: str
    strategy: str
    current_url: str
    title: str
    ranked_links: List[RankedLinkEntity] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "strategy": self.strategy,
            "current_url": self.current_url,
            "title": self.title,
            "ranked_links": [
                {
                    "href": link.href,
                    "text": link.text,
                    "title": link.title,
                    "initial_score": link.initial_score,
                }
                for link in self.ranked_links
            ],
        }
