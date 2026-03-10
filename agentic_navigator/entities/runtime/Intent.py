"""Intent entity - user intent for the gateway/runloop."""

from typing import Any, Dict


class Intent:
    def __init__(self):
        self.user_input: str = ""
        self.session_id: str = ""
        self.source: str = "cli"
        self.metadata: Dict[str, Any] = {}
