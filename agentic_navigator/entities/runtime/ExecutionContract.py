"""ExecutionContract entity - smolhand output."""

from typing import Any, Dict, List, Optional


class ExecutionStep:
    def __init__(self):
        self.tool: str = ""
        self.arguments: Dict[str, Any] = {}
        self.description: str = ""
        self.order: int = 0
        self.depends_on: Optional[int] = None


class ExecutionContract:
    def __init__(self):
        self.steps: List[ExecutionStep] = []
        self.raw_plan: str = ""
        self.declarative_intent: str = ""
        self.imperative_commands: List[str] = []
