"""DOMDescription entity - structured DOM text description."""

from typing import Dict, List


class InteractiveElement:
    def __init__(self):
        self.index: int = 0
        self.tag: str = ""
        self.role: str = ""
        self.text: str = ""
        self.aria_label: str = ""
        self.href: str = ""
        self.element_type: str = ""
        self.is_visible: bool = True
        self.bounding_rect: Dict[str, float] = {}
        self.xpath: str = ""
        self.css_selector: str = ""


class DOMDescription:
    def __init__(self):
        self.page_title: str = ""
        self.page_url: str = ""
        self.headings: List[str] = []
        self.paragraphs: List[str] = []
        self.links: List[Dict[str, str]] = []
        self.buttons: List[Dict[str, str]] = []
        self.inputs: List[Dict[str, str]] = []
        self.forms: List[Dict[str, str]] = []
        self.images: List[Dict[str, str]] = []
        self.interactive_elements: List[InteractiveElement] = []
        self.text_summary: str = ""
        self.structured_text: str = ""
