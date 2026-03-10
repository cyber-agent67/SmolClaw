"""PageDescription entity - merged visual + DOM description."""

from typing import Optional

from agentic_navigator.entities.perception.DOMDescription import DOMDescription
from agentic_navigator.entities.perception.VisualDescription import VisualDescription


class PageDescription:
    def __init__(self):
        self.visual: Optional[VisualDescription] = None
        self.dom: Optional[DOMDescription] = None
        self.merged_description: str = ""
        self.actionable_summary: str = ""
        self.element_map: str = ""
