"""DOMTree entity - pure state container."""

from typing import Any, Dict, List, Optional


class DOMNode:
    def __init__(self):
        self.tag: str = ""
        self.attrs: Dict[str, Any] = {}
        self.children: List["DOMNode"] = []
        self.text_content: Optional[str] = None
        self.node_type: str = "element"


class DOMTree:
    def __init__(self):
        self.root: Optional[DOMNode] = None
        self.raw_html: str = ""
        self.json_string: str = ""
