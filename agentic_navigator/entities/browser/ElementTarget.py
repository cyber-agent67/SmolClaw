"""ElementTarget entity - resolved element on page."""

from typing import Any, Dict, Optional


class ElementTarget:
    def __init__(self):
        self.found: bool = False
        self.tag: str = ""
        self.text: str = ""
        self.xpath: str = ""
        self.css_selector: str = ""
        self.aria_label: str = ""
        self.bounding_box: Dict[str, float] = {}
        self.is_visible: bool = False
        self.is_interactive: bool = False
        self.element_index: int = -1
        self.confidence: float = 0.0
        self.selenium_element: Optional[Any] = None
