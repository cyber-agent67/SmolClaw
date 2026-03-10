"""Plan entity - planner output."""

from typing import List, Optional


class Plan:
    def __init__(self):
        self.requires_tools: bool = False
        self.requires_navigation: bool = False
        self.goal: str = ""
        self.strategy: str = ""
        self.steps_description: List[str] = []
        self.confidence: float = 0.0
        self.done: bool = False
        self.final_answer: Optional[str] = None
