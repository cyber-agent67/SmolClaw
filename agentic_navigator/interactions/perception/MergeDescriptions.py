"""Merge visual and DOM descriptions."""

from agentic_navigator.entities.perception.DOMDescription import DOMDescription
from agentic_navigator.entities.perception.PageDescription import PageDescription
from agentic_navigator.entities.perception.VisualDescription import VisualDescription


class MergeDescriptions:
    @staticmethod
    def execute(visual: VisualDescription, dom: DOMDescription) -> PageDescription:
        merged = PageDescription()
        merged.visual = visual
        merged.dom = dom
        merged.merged_description = (
            f"Title: {dom.page_title}\n"
            f"Visual: {visual.caption}\n"
            f"Top headings: {', '.join(dom.headings[:5])}"
        )
        merged.actionable_summary = merged.merged_description
        return merged
