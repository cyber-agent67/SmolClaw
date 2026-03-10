"""Terminal UI client for smolclaw gateway."""

from __future__ import annotations

import asyncio
import json

from aiohttp import ClientSession, WSMsgType


async def run_tui(url: str) -> None:
    async with ClientSession() as session:
        async with session.ws_connect(url) as ws:
            hello = await ws.receive()
            if hello.type == WSMsgType.TEXT:
                try:
                    payload = json.loads(hello.data)
                    print(payload.get("message", "Connected"))
                except Exception:
                    print("Connected")

            print("smolclaw tui connected. Type your prompt. Type /exit to quit.")

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


def run_tui_sync(url: str) -> None:
    asyncio.run(run_tui(url))
