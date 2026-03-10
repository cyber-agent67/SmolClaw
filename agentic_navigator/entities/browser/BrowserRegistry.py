"""BrowserRegistry entity - pure state container."""

from typing import Any, List


class BrowserRegistry:
    def __init__(self):
        self.active_browsers: List[Any] = []
