"""Service facade for Layer 1 (browser/page/DOM)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from smolclaw.tools.smolhand.layers.layer1_browser.page_operations import (
    BuildBrowserSnapshot,
    ExtractHyperlinks,
    ReadCurrentPage,
)
from smolclaw.tools.smolhand.metrics import measure_latency, record_operation

logger = logging.getLogger(__name__)


class BrowserLayerService:
    """Service facade for Layer 1 browser operations.

    Provides high-level access to raw browser access including:
    - Page state capture (URL, title, page source)
    - Hyperlink extraction
    - DOM tree extraction
    - Browser snapshot building
    """

    @staticmethod
    def current_page_state() -> Dict[str, Any]:
        """Get the current page state (URL, title, page source).

        Returns:
            Dictionary with url, title, and page_source keys
        """
        with measure_latency("layer1.current_page_state"):
            page = ReadCurrentPage.execute()
            record_operation(
                "current_page_state",
                "layer1",
                success=True,
                extra_tags={"url": page.url},
            )
            return {
                "url": page.url,
                "title": page.title,
                "page_source": page.page_source,
            }

    @staticmethod
    def extract_links() -> List[Dict[str, str]]:
        """Extract all hyperlinks from the current page.

        Returns:
            List of dictionaries with href, text, and title for each link
        """
        with measure_latency("layer1.extract_links"):
            links = ExtractHyperlinks.execute()
            record_operation(
                "extract_links",
                "layer1",
                success=True,
                extra_tags={"link_count": str(len(links))},
            )
            return [{"href": l.href, "text": l.text, "title": l.title} for l in links]

    @staticmethod
    def dom_tree_json() -> str:
        """Get the full DOM tree as a JSON string.

        Returns:
            JSON string representation of the DOM tree
        """
        from smolclaw.agent.interactions.dom.GetTree import GetDOMTree

        with measure_latency("layer1.dom_tree"):
            dom_tree = GetDOMTree.execute()
            record_operation("dom_tree", "layer1", success=True)
            return dom_tree.json_string

    @staticmethod
    def page_snapshot_json() -> str:
        """Get a complete browser snapshot as JSON.

        Returns:
            JSON string with page state and extracted links
        """
        with measure_latency("layer1.page_snapshot"):
            snapshot = BuildBrowserSnapshot.execute()
            record_operation(
                "page_snapshot",
                "layer1",
                success=True,
                extra_tags={"link_count": str(len(snapshot.links))},
            )
            return json.dumps(snapshot.as_dict(), indent=2)


__all__ = ["BrowserLayerService"]
