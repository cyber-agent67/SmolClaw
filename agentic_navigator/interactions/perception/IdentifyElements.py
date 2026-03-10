"""Identify element targets from page description."""

from typing import List

from agentic_navigator.entities.browser.ElementTarget import ElementTarget
from agentic_navigator.entities.perception.PageDescription import PageDescription


class IdentifyElements:
    @staticmethod
    def execute(page_description: PageDescription) -> List[ElementTarget]:
        targets: List[ElementTarget] = []
        if page_description.dom:
            for link in page_description.dom.links[:10]:
                target = ElementTarget()
                target.found = True
                target.tag = "a"
                target.text = link.get("text", "")
                target.css_selector = "a"
                target.is_visible = True
                target.is_interactive = True
                target.confidence = 0.5
                targets.append(target)
        return targets
