"""ScoutResult entity - pure state container."""

from typing import List, Optional


class ScoutResult:
    def __init__(self):
        self.best_url: Optional[str] = None
        self.confidence_score: float = 0.0
        self.reason: str = ""
        self.logs: List[str] = []
        self.error: Optional[str] = None
        self.top_links_checked: List[str] = []
