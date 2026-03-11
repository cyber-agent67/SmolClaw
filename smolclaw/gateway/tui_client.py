"""TUI client for SmolClaw Gateway.

Connects to the gateway and provides an interactive terminal UI.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Optional

from aiohttp import ClientSession, WSMsgType


class TUIClient:
    """Terminal UI client for gateway."""
    
    def __init__(self, url: str, session_id: str = "tui"):
        """Initialize TUI client.
        
        Args:
            url: Gateway WebSocket URL
            session_id: Session identifier
        """
        self.url = url
        self.session_id = session_id
    
    async def run(self) -> None:
        """Run the TUI client."""
        async with ClientSession() as session:
            # Connect to gateway
            ws = await session.ws_connect(f"{self.url}?session_id={self.session_id}")
            
            # Handle connection
            async with ws:
                # Wait for welcome message
                hello = await ws.receive()
                if hello.type == WSMsgType.TEXT:
                    try:
                        payload = json.loads(hello.data)
                        print("=" * 70)
                        print(f"  {payload.get('message', 'SmolClaw Gateway Connected')}")
                        print(f"  Session: {payload.get('session_id', 'unknown')}")
                        print(f"  Interfaces: {', '.join(payload.get('interfaces', []))}")
                        print("=" * 70)
                        print()
                        print("Commands:")
                        print("  /state  - Show cognitive state")
                        print("  /replay - Replay events")
                        print("  /exit   - Exit")
                        print()
                    except Exception:
                        print("Connected to gateway")
                
                # Main loop
                while True:
                    try:
                        # Get user input
                        prompt = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: input("cognitive> ").strip()
                        )
                        
                        if not prompt:
                            continue
                        
                        if prompt in {"/exit", "exit", "quit"}:
                            print("Goodbye!")
                            return
                        
                        if prompt == "/state":
                            await ws.send_json({"type": "state"})
                        elif prompt == "/replay":
                            await ws.send_json({"type": "replay"})
                        else:
                            # Process intent
                            await ws.send_json({
                                "type": "process",
                                "prompt": prompt,
                            })
                        
                        # Wait for response
                        reply = await ws.receive()
                        
                        if reply.type == WSMsgType.TEXT:
                            try:
                                payload = json.loads(reply.data)
                                self._display_response(payload)
                            except Exception as e:
                                print(f"Error parsing response: {e}")
                                print(reply.data)
                        elif reply.type in {WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED}:
                            print("\nGateway disconnected")
                            return
                        elif reply.type == WSMsgType.ERROR:
                            print(f"\nConnection error")
                            return
                    
                    except KeyboardInterrupt:
                        print("\nGoodbye!")
                        return
                    except EOFError:
                        print("\nGoodbye!")
                        return
    
    def _display_response(self, payload: dict) -> None:
        """Display gateway response.
        
        Args:
            payload: Response payload
        """
        msg_type = payload.get("type", "unknown")
        
        if msg_type == "result":
            result = payload.get("result", {})
            
            # Show result
            if result.get("success"):
                print(f"\n✓ {result.get('result', 'Success')}")
            elif result.get("requires_clarification"):
                print(f"\n? Clarification needed")
                plan = result.get("plan", {})
                print(f"  Strategy: {plan.get('strategy', 'unknown')}")
                print(f"  Confidence: {plan.get('confidence', 0):.2f}")
            else:
                print(f"\n✗ {result.get('error', 'Unknown error')}")
            
            # Show state summary
            state = payload.get("session_state", {})
            agent_state = state.get("agent_state", {})
            if isinstance(agent_state, dict):
                print(f"  State: {agent_state.get('state', 'unknown')}")
        
        elif msg_type == "state":
            state = payload.get("state", {})
            print("\n" + "=" * 70)
            print("  Cognitive State")
            print("=" * 70)
            print(json.dumps(state, indent=2, default=str))
        
        elif msg_type == "replay":
            events = payload.get("events", [])
            print("\n" + "=" * 70)
            print(f"  Event Replay ({len(events)} events)")
            print("=" * 70)
            for event in events:
                event_type = event.get("event_type", "unknown")
                metadata = event.get("metadata", {})
                print(f"  • {event_type}: {json.dumps(metadata, default=str)[:100]}")
        
        elif msg_type == "error":
            print(f"\n✗ Error: {payload.get('message', 'Unknown error')}")
        
        elif msg_type == "pong":
            pass  # Ignore pong
        
        else:
            print(f"\n? Unknown response type: {msg_type}")


def run_tui_sync(url: str, session_id: str = "tui") -> None:
    """Run TUI client synchronously.
    
    Args:
        url: Gateway WebSocket URL
        session_id: Session identifier
    """
    client = TUIClient(url, session_id)
    asyncio.run(client.run())


def main() -> None:
    """Main TUI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmolClaw TUI Client")
    parser.add_argument("--url", default="ws://127.0.0.1:8765/ws", help="Gateway URL")
    parser.add_argument("--session", default="tui", help="Session ID")
    
    args = parser.parse_args()
    
    try:
        run_tui_sync(args.url, args.session)
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the gateway is running: smolclaw gateway start")
        sys.exit(1)


if __name__ == "__main__":
    main()
