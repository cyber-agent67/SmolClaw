"""Interactions for Layer 1 (browser/page/DOM)."""

from __future__ import annotations

from helium import get_driver

from browser_subagents.layers.layer1_browser.entities import BrowserSnapshotEntity, LinkEntity, PageStateEntity


class ReadCurrentPage:
    @staticmethod
    def execute() -> PageStateEntity:
        driver = get_driver()
        return PageStateEntity(
            url=driver.current_url,
            title=driver.title,
            page_source=driver.page_source,
        )


class ExtractHyperlinks:
    @staticmethod
    def execute() -> list[LinkEntity]:
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
    @staticmethod
    def execute() -> BrowserSnapshotEntity:
        page = ReadCurrentPage.execute()
        links = ExtractHyperlinks.execute()
        return BrowserSnapshotEntity(page=page, links=links)
