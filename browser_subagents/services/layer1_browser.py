"""Service facade for Layer 1 (browser/page/DOM)."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from browser_subagents.layers.layer1_browser.interactions import BuildBrowserSnapshot, ExtractHyperlinks, ReadCurrentPage


class BrowserLayerService:
	@staticmethod
	def current_page_state() -> Dict[str, Any]:
		page = ReadCurrentPage.execute()
		return {
			"url": page.url,
			"title": page.title,
			"page_source": page.page_source,
		}

	@staticmethod
	def extract_links() -> List[Dict[str, str]]:
		links = ExtractHyperlinks.execute()
		return [{"href": l.href, "text": l.text, "title": l.title} for l in links]

	@staticmethod
	def dom_tree_json() -> str:
		from agentic_navigator.interactions.dom.GetTree import GetDOMTree

		dom_tree = GetDOMTree.execute()
		return dom_tree.json_string

	@staticmethod
	def page_snapshot_json() -> str:
		snapshot = BuildBrowserSnapshot.execute()
		return json.dumps(snapshot.as_dict(), indent=2)
__all__ = ["BrowserLayerService"]
