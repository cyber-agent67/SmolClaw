"""Terminal UI client for smolclaw gateway.

This module exists as a stable import path to avoid naming conflicts between
`smolclaw/gateway.py` (module) and `smolclaw/gateway/` (directory).
"""

from __future__ import annotations

import asyncio
import json

from aiohttp import ClientSession, WSMsgType


async def run_tui(url: str) -> None:
    async with ClientSession() as session:
        last_error: Exception | None = None
        for _ in range(10):
            try:
                ws = await session.ws_connect(url)
                break
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.3)
        else:
            print(f"Unable to connect to assistant gateway at {url}: {last_error}")
            print("Try: smolclaw gateway start")
            return

        try:
            async with ws:
                hello = await ws.receive()
                if hello.type == WSMsgType.TEXT:
                    try:
                        payload = json.loads(hello.data)
                        print(payload.get("message", "Connected"))
                    except Exception:
                        print("Connected")

                print("smolclaw assistant ready. Type your command. Type /exit to quit.")

                while True:
                    prompt = input("smolclaw> ").strip()
                    if not prompt:
                        continue
                    if prompt in {"/exit", "exit", "quit"}:
                        print("bye")
                        return

                    await ws.send_json({"type": "run_prompt", "prompt": prompt})
                    reply = await ws.receive()

                    if reply.type == WSMsgType.TEXT:
                        try:
                            payload = json.loads(reply.data)
                            if payload.get("type") == "result":
                                print(payload.get("result", ""))
                            else:
                                print(payload)
                        except Exception:
                            print(reply.data)
                    elif reply.type in {WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.CLOSED}:
                        print("Gateway disconnected")
                        return
        except Exception as exc:
            print(f"Unable to connect to assistant gateway at {url}: {exc}")
            print("Try: smolclaw gateway start")


def run_tui_sync(url: str) -> None:
    asyncio.run(run_tui(url))
