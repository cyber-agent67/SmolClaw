"""Page operations for Layer 1 (browser/page/DOM)."""

from __future__ import annotations

from typing import List

from helium import get_driver

from smolclaw.smolhand.layers.layer1_browser.page_state import (
    BrowserSnapshotEntity,
    LinkEntity,
    PageStateEntity,
)


class ReadCurrentPage:
    """Reads the current page state from the browser."""

    @staticmethod
    def execute() -> PageStateEntity:
        """Execute the read operation and return page state."""
        driver = get_driver()
        return PageStateEntity(
            url=driver.current_url,
            title=driver.title,
            page_source=driver.page_source,
        )


class ExtractHyperlinks:
    """Extracts all hyperlinks from the current page."""

    @staticmethod
    def execute() -> List[LinkEntity]:
        """Execute hyperlink extraction and return list of links."""
        driver = get_driver()
        links = driver.execute_script(
            """
            var links = Array.from(document.querySelectorAll('a[href]'));
            return links.map(function(link) {
                return {
                    href: link.href,
                    text: link.innerText.trim(),
                    title: link.title || ''
                };
            });
            """
        )
        return [
            LinkEntity(
                href=item.get("href", ""),
                text=item.get("text", ""),
                title=item.get("title", ""),
            )
            for item in (links or [])
        ]


class BuildBrowserSnapshot:
    """Builds a complete browser snapshot including page state and links."""

    @staticmethod
    def execute() -> BrowserSnapshotEntity:
        """Execute snapshot building and return complete browser state."""
        page = ReadCurrentPage.execute()
        links = ExtractHyperlinks.execute()
        return BrowserSnapshotEntity(page=page, links=links)
