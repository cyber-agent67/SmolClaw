"""WebSocket gateway for smolclaw."""

from __future__ import annotations

import argparse
import asyncio
import json

from aiohttp import web

from smolclaw.config import load_config
from smolhand import OpenAICompatClient, SmolhandRunner, default_tools


HUGGINGFACE_BASE_URL = "https://router.huggingface.co/v1"
HUGGINGFACE_DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def _build_runner() -> SmolhandRunner:
    cfg = load_config()
    model = cfg.get("model", HUGGINGFACE_DEFAULT_MODEL)
    base_url = cfg.get("base_url", HUGGINGFACE_BASE_URL)
    api_key = cfg.get("api_key") or cfg.get("hf_token", "")

    llm = OpenAICompatClient(model=model, base_url=base_url, api_key=api_key)
    return SmolhandRunner(llm_client=llm, tools=default_tools())


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    await ws.send_json({"type": "hello", "message": "smolclaw gateway ready"})

    runner = _build_runner()

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
            except Exception:
                await ws.send_json({"type": "error", "message": "Invalid JSON payload"})
                continue

            event_type = data.get("type")
            if event_type == "ping":
                await ws.send_json({"type": "pong"})
                continue

            if event_type == "run_prompt":
                prompt = data.get("prompt", "")
                if not prompt:
                    await ws.send_json({"type": "error", "message": "prompt is required"})
                    continue

                # Blocking LLM call in thread so ws loop stays responsive.
                result = await asyncio.to_thread(runner.run, prompt)
                await ws.send_json({"type": "result", "result": result})
                continue

            await ws.send_json({"type": "error", "message": f"Unknown event type: {event_type}"})

        elif msg.type == web.WSMsgType.ERROR:
            break

    return ws


async def run_server(host: str, port: int) -> None:
    app = web.Application()
    app.router.add_get("/ws", ws_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()

    print(f"smolclaw gateway listening on ws://{host}:{port}/ws")
    stop_event = asyncio.Event()
    await stop_event.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="smolclaw websocket gateway")
    parser.add_argument("serve", nargs="?", default="serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    asyncio.run(run_server(args.host, args.port))


if __name__ == "__main__":
    main()
