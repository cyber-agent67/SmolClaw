"""SmolClaw Gateway package.

This package provides WebSocket gateway and REST API functionality:
- WebSocket server for smolclaw agent access
- REST API for Chronicle SSPM features
- TUI client for gateway interaction
"""

from smolclaw.gateway.client import run_tui_sync
from smolclaw.gateway.server import main as run_server

__all__ = [
    "run_tui_sync",
    "run_server",
]
