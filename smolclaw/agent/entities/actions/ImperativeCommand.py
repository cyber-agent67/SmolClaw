"""ImperativeCommand entity - low-level browser command."""

from typing import Any, Dict, Optional


class ImperativeCommand:
    def __init__(self):
        self.command_type: str = ""
        self.selector: str = ""
        self.selector_type: str = "css"
        self.value: Optional[str] = None
        self.xpath: str = ""
        self.text_match: str = ""
        self.coordinates: Optional[Dict[str, float]] = None
        self.helium_action: str = ""
        self.fallback_strategy: str = ""
        self.executed: bool = False
        self.result: str = ""
        self.error: Optional[str] = None
