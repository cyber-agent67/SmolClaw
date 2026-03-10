"""DeclarativeAction entity - high-level natural language action."""

from typing import Any, Dict, Optional


class DeclarativeAction:
    def __init__(self):
        self.intent: str = ""
        self.target_description: str = ""
        self.value: Optional[str] = None
        self.action_type: str = ""
        self.raw_instruction: str = ""
        self.confidence: float = 0.0
        self.metadata: Dict[str, Any] = {}
