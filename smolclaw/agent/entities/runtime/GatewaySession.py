"""GatewaySession entity - websocket session state."""

from typing import Any, Dict, List, Optional


class GatewaySession:
    def __init__(self):
        self.session_id: str = ""
        self.connected_at: str = ""
        self.last_activity: str = ""
        self.message_history: List[Dict[str, str]] = []
        self.is_active: bool = False
        self.websocket: Optional[Any] = None
