"""Page state entities for Layer 1 (browser/page/DOM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PageStateEntity:
    """Represents the state of a web page."""
    url: str
    title: str
    page_source: str


@dataclass
class LinkEntity:
    """Represents a hyperlink on a web page."""
    href: str
    text: str
    title: str


@dataclass
class BrowserSnapshotEntity:
    """Represents a complete snapshot of browser state including page and links."""
    page: PageStateEntity
    links: List[LinkEntity] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.page.url,
            "title": self.page.title,
            "page_source": self.page.page_source,
            "links": [
                {
                    "href": link.href,
                    "text": link.text,
                    "title": link.title,
                }
                for link in self.links
            ],
        }
