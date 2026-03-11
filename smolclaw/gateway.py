"""WebSocket gateway for smolclaw."""

from __future__ import annotations

import argparse
import asyncio
import json

from aiohttp import web

from smolclaw.config import load_config
from smolhand import OpenAICompatClient, SmolhandRunner, default_tools

# ---------------------------------------------------------------------------
# Chronicle SSPM REST API (FastAPI)
# ---------------------------------------------------------------------------
try:
    from fastapi import FastAPI
    import uvicorn

    from api import agents_router, scans_router, settings_router, saas_router

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


def build_api_app() -> "FastAPI":
    """Create the FastAPI application with Chronicle SSPM routers."""
    if not _HAS_FASTAPI:
        raise RuntimeError(
            "FastAPI is not installed. Install it with: pip install fastapi uvicorn"
        )

    app = FastAPI(
        title="SmolClaw Chronicle SSPM API",
        version="0.1.0",
        description="REST API for Chronicle SSPM features — agents, scans, settings, and SaaS management.",
    )

    # Register Chronicle API routers under /api/v1/
    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(scans_router, prefix="/api/v1")
    app.include_router(settings_router, prefix="/api/v1")
    app.include_router(saas_router, prefix="/api/v1")

    @app.get("/api/v1/health")
    async def health():
        return {"status": "ok", "service": "smolclaw-chronicle-sspm"}

    return app


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


async def run_server(host: str, port: int, api_port: int = 0) -> None:
    # --- aiohttp WebSocket server ---
    app = web.Application()
    app.router.add_get("/ws", ws_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()

    print(f"smolclaw gateway listening on ws://{host}:{port}/ws")

    # --- FastAPI REST API server (Chronicle SSPM) ---
    if _HAS_FASTAPI and api_port:
        api_app = build_api_app()
        config = uvicorn.Config(
            api_app, host=host, port=api_port, log_level="info",
        )
        server = uvicorn.Server(config)
        print(f"smolclaw REST API listening on http://{host}:{api_port}/api/v1/")
        # Run uvicorn in a background task so both servers share the event loop.
        asyncio.create_task(server.serve())
    elif api_port and not _HAS_FASTAPI:
        print("WARNING: --api-port given but fastapi/uvicorn not installed; REST API disabled.")

    stop_event = asyncio.Event()
    await stop_event.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="smolclaw websocket gateway")
    parser.add_argument("serve", nargs="?", default="serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--api-port",
        type=int,
        default=8766,
        help="Port for the Chronicle SSPM REST API (0 to disable)",
    )
    args = parser.parse_args()

    asyncio.run(run_server(args.host, args.port, api_port=args.api_port))


if __name__ == "__main__":
    main()
