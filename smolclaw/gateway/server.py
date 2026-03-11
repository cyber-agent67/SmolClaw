"""Gateway server for SmolClaw cognitive system.

This gateway supports multiple interfaces:
- TUI (Terminal UI)
- CLI (Command Line)
- Telegram (Future)
- WebSockets (API)

All interfaces connect through this unified gateway.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from aiohttp import web

from smolclaw.cognitive_loop import CognitiveLoop
from smolclaw.config import load_config


# =============================================================================
# Gateway Configuration
# =============================================================================

HUGGINGFACE_BASE_URL = "https://router.huggingface.co/v1"
HUGGINGFACE_DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


# =============================================================================
# Cognitive Session Manager
# =============================================================================

class CognitiveSession:
    """Manages a cognitive session for a client connection."""
    
    def __init__(
        self,
        session_id: str,
        persistence_path: Optional[str] = None,
        max_loops: int = 10,
    ):
        """Initialize cognitive session.
        
        Args:
            session_id: Unique session identifier
            persistence_path: Optional path for event persistence
            max_loops: Maximum execution loops
        """
        self.session_id = session_id
        self.loop = CognitiveLoop(
            persistence_path=persistence_path,
            max_loops=max_loops,
        )
        self.created_at = asyncio.get_event_loop().time()
        self.last_activity = self.created_at
        self.request_count = 0
    
    def process(self, intent: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process intent through cognitive loop.
        
        Args:
            intent: User intent/goal
            context: Optional context
            
        Returns:
            Cognitive processing result
        """
        self.last_activity = asyncio.get_event_loop().time()
        self.request_count += 1
        return self.loop.process_intent(intent, context)
    
    def get_state(self) -> Dict[str, Any]:
        """Get session state.
        
        Returns:
            Session state dictionary
        """
        return {
            "session_id": self.session_id,
            "agent_state": self.loop.get_state(),
            "request_count": self.request_count,
            "uptime": asyncio.get_event_loop().time() - self.created_at,
        }
    
    def replay(self, from_version: int = 0) -> list:
        """Replay session events.
        
        Args:
            from_version: Starting version
            
        Returns:
            List of events
        """
        return self.loop.replay(from_version)


class SessionManager:
    """Manages multiple cognitive sessions."""
    
    def __init__(self, persistence_base: Optional[str] = None):
        """Initialize session manager.
        
        Args:
            persistence_base: Base path for session persistence
        """
        self.sessions: Dict[str, CognitiveSession] = {}
        self.persistence_base = Path(persistence_base) if persistence_base else None
        self.max_sessions = 100
        self.session_timeout = 3600  # 1 hour
    
    def get_or_create_session(self, session_id: str) -> CognitiveSession:
        """Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Cognitive session
        """
        if session_id not in self.sessions:
            # Create persistence path for session
            persistence_path = None
            if self.persistence_base:
                persistence_path = str(self.persistence_base / session_id)
                os.makedirs(persistence_path, exist_ok=True)
            
            # Create new session
            self.sessions[session_id] = CognitiveSession(
                session_id=session_id,
                persistence_path=persistence_path,
            )
            
            # Cleanup old sessions if at limit
            if len(self.sessions) >= self.max_sessions:
                self._cleanup_old_sessions()
        
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[CognitiveSession]:
        """Get existing session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Cognitive session or None
        """
        return self.sessions.get(session_id)
    
    def _cleanup_old_sessions(self) -> None:
        """Remove sessions that have timed out."""
        now = asyncio.get_event_loop().time()
        expired = [
            sid for sid, session in self.sessions.items()
            if (now - session.last_activity) > self.session_timeout
        ]
        
        for sid in expired:
            del self.sessions[sid]


# =============================================================================
# Gateway Application
# =============================================================================

class GatewayApp:
    """Gateway application with multiple interface support."""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        api_port: int = 8766,
        persistence_path: Optional[str] = None,
    ):
        """Initialize gateway.
        
        Args:
            host: Host to bind to
            port: WebSocket port
            api_port: REST API port
            persistence_path: Base path for persistence
        """
        self.host = host
        self.port = port
        self.api_port = api_port
        self.session_manager = SessionManager(persistence_path)
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup web routes."""
        # WebSocket endpoint
        self.app.router.add_get("/ws", self.ws_handler)
        
        # REST API endpoints
        self.app.router.add_post("/api/v1/process", self.process_handler)
        self.app.router.add_get("/api/v1/session/{session_id}", self.session_handler)
        self.app.router.add_get("/api/v1/replay/{session_id}", self.replay_handler)
        self.app.router.add_get("/api/v1/health", self.health_handler)
    
    async def ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections (TUI, CLI, Telegram).
        
        Args:
            request: Web request
            
        Returns:
            WebSocket response
        """
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)
        
        # Get or create session
        session_id = request.query.get("session_id", "default")
        session = self.session_manager.get_or_create_session(session_id)
        
        # Send welcome message
        await ws.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "SmolClaw Gateway Ready",
            "interfaces": ["tui", "cli", "telegram"],
        })
        
        # Handle messages
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    result = await self._handle_message(data, session)
                    await ws.send_json(result)
                except Exception as e:
                    await ws.send_json({
                        "type": "error",
                        "message": str(e),
                    })
            elif msg.type == web.WSMsgType.ERROR:
                break
        
        return ws
    
    async def _handle_message(
        self,
        data: dict,
        session: CognitiveSession
    ) -> dict:
        """Handle incoming message.
        
        Args:
            data: Message data
            session: Cognitive session
            
        Returns:
            Response data
        """
        event_type = data.get("type", "process")
        
        if event_type == "ping":
            return {"type": "pong"}
        
        elif event_type == "process":
            intent = data.get("prompt", data.get("intent", ""))
            if not intent:
                return {
                    "type": "error",
                    "message": "prompt or intent is required",
                }
            
            # Process through cognitive loop
            result = session.process(intent)
            
            return {
                "type": "result",
                "result": result,
                "session_state": session.get_state(),
            }
        
        elif event_type == "state":
            return {
                "type": "state",
                "state": session.get_state(),
            }
        
        elif event_type == "replay":
            from_version = data.get("from_version", 0)
            events = session.replay(from_version)
            return {
                "type": "replay",
                "events": events,
            }
        
        else:
            return {
                "type": "error",
                "message": f"Unknown event type: {event_type}",
            }
    
    async def process_handler(self, request: web.Request) -> web.Response:
        """Handle REST API process request.
        
        Args:
            request: Web request
            
        Returns:
            JSON response
        """
        try:
            data = await request.json()
        except Exception:
            return web.json_response({
                "error": "Invalid JSON",
            }, status=400)
        
        session_id = data.get("session_id", "default")
        session = self.session_manager.get_or_create_session(session_id)
        
        intent = data.get("intent", "")
        if not intent:
            return web.json_response({
                "error": "intent is required",
            }, status=400)
        
        result = session.process(intent)
        
        return web.json_response({
            "session_id": session_id,
            "result": result,
            "state": session.get_state(),
        })
    
    async def session_handler(self, request: web.Request) -> web.Response:
        """Handle session state request.
        
        Args:
            request: Web request
            
        Returns:
            JSON response
        """
        session_id = request.match_info["session_id"]
        session = self.session_manager.get_session(session_id)
        
        if not session:
            return web.json_response({
                "error": "Session not found",
            }, status=404)
        
        return web.json_response(session.get_state())
    
    async def replay_handler(self, request: web.Request) -> web.Response:
        """Handle event replay request.
        
        Args:
            request: Web request
            
        Returns:
            JSON response
        """
        session_id = request.match_info["session_id"]
        from_version = int(request.query.get("from_version", 0))
        
        session = self.session_manager.get_session(session_id)
        if not session:
            return web.json_response({
                "error": "Session not found",
            }, status=404)
        
        events = session.replay(from_version)
        
        return web.json_response({
            "session_id": session_id,
            "from_version": from_version,
            "events": events,
        })
    
    async def health_handler(self, request: web.Request) -> web.Response:
        """Handle health check request.
        
        Returns:
            JSON response
        """
        return web.json_response({
            "status": "ok",
            "service": "smolclaw-gateway",
            "sessions": len(self.session_manager.sessions),
        })
    
    async def run(self) -> None:
        """Run the gateway server."""
        from aiohttp import web
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        # Start WebSocket server
        ws_site = web.TCPSite(runner, self.host, self.port)
        await ws_site.start()
        
        print(f"✓ Gateway WebSocket: ws://{self.host}:{self.port}/ws")
        print(f"✓ Gateway REST API: http://{self.host}:{self.api_port}/api/v1/")
        print(f"✓ Interfaces: TUI, CLI, Telegram")
        print(f"✓ Persistence: {self.session_manager.persistence_base or 'disabled'}")
        
        # Keep running
        stop_event = asyncio.Event()
        await stop_event.wait()


# =============================================================================
# CLI Entry Point
# =============================================================================

def main() -> None:
    """Main gateway entry point."""
    parser = argparse.ArgumentParser(description="SmolClaw Gateway")
    parser.add_argument("serve", nargs="?", default="serve", help="Command to run")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket port")
    parser.add_argument("--api-port", type=int, default=8766, help="REST API port")
    parser.add_argument("--persistence", type=str, default=None, help="Persistence path")
    
    args = parser.parse_args()
    
    # Load config for defaults
    cfg = load_config()
    host = args.host or cfg.get("gateway_host", "127.0.0.1")
    port = args.port or int(cfg.get("gateway_port", 8765))
    api_port = args.api_port or int(cfg.get("gateway_api_port", 8766))
    
    # Run gateway
    gateway = GatewayApp(
        host=host,
        port=port,
        api_port=api_port,
        persistence_path=args.persistence,
    )
    
    try:
        asyncio.run(gateway.run())
    except KeyboardInterrupt:
        print("\n✓ Gateway stopped")


if __name__ == "__main__":
    main()
