"""PageState entity - full state of current page."""

from typing import Any, Dict, List, Optional

from PIL import Image


class PageState:
    def __init__(self):
        self.url: str = ""
        self.title: str = ""
        self.screenshot: Optional[Image.Image] = None
        self.screenshot_base64: str = ""
        self.dom_html: str = ""
        self.dom_json: str = ""
        self.viewport_width: int = 0
        self.viewport_height: int = 0
        self.timestamp: str = ""
        self.interactive_elements: List[Dict[str, Any]] = []
