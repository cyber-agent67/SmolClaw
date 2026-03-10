"""NavigationStack entity - pure state container."""

from typing import List


class NavigationStack:
    def __init__(self):
        self.stack: List[str] = []
