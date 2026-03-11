"""Exploration tool entities for AI Agent A* DOM exploration.

This module provides state containers for A* heuristic link exploration.
The exploration tool is used by the AI Agent to find relevant links.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RankedLinkEntity:
    """Represents a hyperlink with its A* exploration score.

    Attributes:
        href: Link URL
        text: Link text content
        title: Link title attribute
        initial_score: A* heuristic score for this link
    """
    href: str
    text: str
    title: str
    initial_score: float


@dataclass
class ExplorationResultEntity:
    """Represents the result of A* DOM exploration on a page.

    Attributes:
        target: Target description that was searched for
        strategy: Exploration strategy used ("a_star")
        current_url: Current page URL where exploration was performed
        title: Current page title
        ranked_links: List of top-k ranked links with scores
    """
    target: str
    strategy: str
    current_url: str
    title: str
    ranked_links: List[RankedLinkEntity] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
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


__all__ = ["RankedLinkEntity", "ExplorationResultEntity"]
