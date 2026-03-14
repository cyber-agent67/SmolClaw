"""Tab entity - pure state container."""

from typing import List, Optional


class Tab:
    def __init__(self):
        self.id: str = ""
        self.url: Optional[str] = None
        self.history: List[str] = []
        self.active: bool = False
        self.window_handle: Optional[str] = None
