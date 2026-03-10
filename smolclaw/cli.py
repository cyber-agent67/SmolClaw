"""smolclaw command line interface."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from typing import List

import click

from smolclaw.config import load_config, log_path, pid_path, save_config
from smolclaw.gateway_tui_client import run_tui_sync


HUGGINGFACE_BASE_URL = "https://router.huggingface.co/v1"
HUGGINGFACE_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "meta-llama/Llama-3.1-8B-Instruct",
    "HuggingFaceTB/SmolLM3-3B",
]


@click.group(
    help=(
        "SMOL claw CLI\n\n"
        "Core commands:\n"
        "  smolclaw onboard                Interactive Hugging Face setup and login\n"
        "  smolclaw tui                    Personal assistant shell (recommended)\n"
        "  smolclaw gateway start|stop|restart\n"
    )
)
def main() -> None:
    pass


@main.command(help="Interactive onboarding for Hugging Face model selection and login.")
def onboard() -> None:
    cfg = load_config()

    click.echo("Using Hugging Face as the only provider for now.")
    models: List[str] = HUGGINGFACE_MODELS
    click.echo("Available model suggestions:")
    for idx, name in enumerate(models, start=1):
        click.echo(f"  {idx}. {name}")

    model = click.prompt("Choose model", default=cfg.get("model", models[0] if models else ""))

    base_url = click.prompt(
        "Hugging Face OpenAI-compatible base URL",
        default=cfg.get("base_url", HUGGINGFACE_BASE_URL),
        show_default=True,
    )

    hf_token = cfg.get("hf_token", "")
    hf_token = click.prompt("Hugging Face token", default=hf_token, hide_input=True)
    try:
        from huggingface_hub import login

        login(token=hf_token, add_to_git_credential=False)
        click.echo("Hugging Face login successful.")
    except Exception as e:
        raise click.ClickException(f"Hugging Face login failed: {e}") from e

    cfg.update(
        {
            "provider": "huggingface",
            "model": model,
            "base_url": base_url,
            "api_key": hf_token,
            "hf_token": hf_token,
        }
    )
    save_config(cfg)
    click.echo("Onboarding complete. Hugging Face configuration saved.")


@main.group(help="Manage smolclaw websocket gateway.")
def gateway() -> None:
    pass


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _start_gateway_process(host: str, port: int) -> tuple[int, bool]:
    """Starts gateway if needed and returns (pid, started_now)."""
    pid_file = pid_path()
    if pid_file.exists():
        existing = int(pid_file.read_text(encoding="utf-8").strip())
        if _is_running(existing):
            return existing, False
        pid_file.unlink(missing_ok=True)

    log_file = open(log_path(), "a", encoding="utf-8")
    cmd = [sys.executable, "-m", "smolclaw.gateway", "serve", "--host", host, "--port", str(port)]

    proc = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    pid_file.write_text(str(proc.pid), encoding="utf-8")
    return proc.pid, True


@gateway.command("start", help="Start websocket gateway in background.")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8765, type=int, show_default=True)
def gateway_start(host: str, port: int) -> None:
    pid, started_now = _start_gateway_process(host, port)

    cfg = load_config()
    cfg.update({"gateway_host": host, "gateway_port": port})
    save_config(cfg)

    if started_now:
        click.echo(f"Gateway started (pid={pid}) at ws://{host}:{port}/ws")
    else:
        click.echo(f"Gateway already running (pid={pid})")


@gateway.command("stop", help="Stop websocket gateway.")
def gateway_stop() -> None:
    pid_file = pid_path()
    if not pid_file.exists():
        click.echo("Gateway is not running.")
        return

    pid = int(pid_file.read_text(encoding="utf-8").strip())
    if not _is_running(pid):
        pid_file.unlink(missing_ok=True)
        click.echo("Gateway pid file existed, but process was not running.")
        return

    os.kill(pid, signal.SIGTERM)
    pid_file.unlink(missing_ok=True)
    click.echo(f"Gateway stopped (pid={pid})")


@gateway.command("restart", help="Restart websocket gateway.")
@click.option("--host", default=None)
@click.option("--port", default=None, type=int)
def gateway_restart(host: str | None, port: int | None) -> None:
    cfg = load_config()
    chosen_host = host or cfg.get("gateway_host", "127.0.0.1")
    chosen_port = port or int(cfg.get("gateway_port", 8765))
    ctx = click.get_current_context()
    ctx.invoke(gateway_stop)
    ctx.invoke(gateway_start, host=chosen_host, port=chosen_port)


@gateway.command("status", help="Show websocket gateway status.")
def gateway_status() -> None:
    pid_file = pid_path()
    cfg = load_config()
    host = cfg.get("gateway_host", "127.0.0.1")
    port = int(cfg.get("gateway_port", 8765))

    if not pid_file.exists():
        click.echo("Gateway status: stopped")
        click.echo(f"Expected endpoint: ws://{host}:{port}/ws")
        return

    pid = int(pid_file.read_text(encoding="utf-8").strip())
    if _is_running(pid):
        click.echo(f"Gateway status: running (pid={pid})")
        click.echo(f"Endpoint: ws://{host}:{port}/ws")
    else:
        click.echo("Gateway status: stale pid file")


@main.command(help="Start personal assistant TUI (auto-connects to gateway).")
@click.option("--url", default=None, help="WebSocket URL (default from onboarding/gateway config)")
@click.option(
    "--ensure-gateway/--no-ensure-gateway",
    default=True,
    show_default=True,
    help="Auto-start local websocket gateway when using default URL.",
)
def tui(url: str | None, ensure_gateway: bool) -> None:
    cfg = load_config()
    host = cfg.get("gateway_host", "127.0.0.1")
    port = int(cfg.get("gateway_port", 8765))
    ws_url = url or f"ws://{host}:{port}/ws"

    if ensure_gateway and url is None:
        pid, started_now = _start_gateway_process(host, port)
        if started_now:
            click.echo(f"Started assistant gateway (pid={pid})")

    run_tui_sync(ws_url)


if __name__ == "__main__":
    main()
