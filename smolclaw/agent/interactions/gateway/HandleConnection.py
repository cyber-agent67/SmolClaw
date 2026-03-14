"""Handle gateway connection interaction."""

import uuid
from datetime import datetime

from smolclaw.agent.entities.runtime.GatewaySession import GatewaySession


class HandleConnection:
    @staticmethod
    def execute(websocket) -> GatewaySession:
        session = GatewaySession()
        session.session_id = str(uuid.uuid4())
        session.connected_at = datetime.utcnow().isoformat() + "Z"
        session.last_activity = session.connected_at
        session.is_active = True
        session.websocket = websocket
        return session
