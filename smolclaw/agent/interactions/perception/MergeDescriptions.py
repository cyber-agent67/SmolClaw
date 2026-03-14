"""Merge visual and DOM descriptions."""

from smolclaw.agent.entities.perception.DOMDescription import DOMDescription
from smolclaw.agent.entities.perception.PageDescription import PageDescription
from smolclaw.agent.entities.perception.VisualDescription import VisualDescription


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
