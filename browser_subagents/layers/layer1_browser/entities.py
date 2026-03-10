"""Entities for Layer 1 (browser/page/DOM)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PageStateEntity:
    url: str
    title: str
    page_source: str


@dataclass
class LinkEntity:
    href: str
    text: str
    title: str


@dataclass
class BrowserSnapshotEntity:
    page: PageStateEntity
    links: List[LinkEntity] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
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
