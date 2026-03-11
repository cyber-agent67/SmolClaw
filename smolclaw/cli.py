"""smolclaw command line interface."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import click

from smolclaw.config import (
    HUGGINGFACE_BASE_URL,
    HUGGINGFACE_MODELS,
    config_path,
    ensure_home_layout,
    load_config,
    log_path,
    mcp_dir,
    pid_path,
    save_config,
    smolclaw_home_dir,
    workplace_dir,
)
from smolclaw.gateway.client import run_tui_sync


@click.group(
    help=(
        "SMOL claw CLI\n\n"
        "Core commands:\n"
        "  smolclaw setup                    One-command setup with all options\n"
        "  smolclaw onboard                  Interactive Hugging Face setup and login\n"
        "  smolclaw tui                      Personal assistant shell (recommended)\n"
        "  smolclaw gateway start|stop|restart\n"
    )
)
def main() -> None:
    pass


@main.command("setup", help="One-command setup with all configuration options.")
@click.option("--provider", default="huggingface", type=click.Choice(["huggingface"]), help="LLM provider")
@click.option("--model", default=None, help="Model name (e.g., Qwen/Qwen2.5-7B-Instruct)")
@click.option("--base-url", default=None, help="API base URL")
@click.option("--api-key", default=None, help="API key or token")
@click.option("--hf-token", default=None, help="Hugging Face token (if using HF)")
@click.option("--headless/--no-headless", default=False, help="Run browser in headless mode")
@click.option("--gateway-host", default="127.0.0.1", help="Gateway host")
@click.option("--gateway-port", default=8765, type=int, help="Gateway port")
@click.option("--start-gateway/--no-start-gateway", default=True, help="Start gateway after setup")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def setup(
    provider: str,
    model: Optional[str],
    base_url: Optional[str],
    api_key: Optional[str],
    hf_token: Optional[str],
    headless: bool,
    gateway_host: str,
    gateway_port: int,
    start_gateway: bool,
    verbose: bool,
) -> None:
    """Complete one-command setup for SmolClaw.
    
    Examples:
    
    \b
    # Quick setup with defaults (Qwen model on Hugging Face)
    smolclaw setup --hf-token YOUR_TOKEN
    
    \b
    # Full setup with all options
    smolclaw setup \\
        --provider huggingface \\
        --model Qwen/Qwen2.5-7B-Instruct \\
        --base-url https://router.huggingface.co/v1 \\
        --hf-token YOUR_TOKEN \\
        --headless \\
        --gateway-host 127.0.0.1 \\
        --gateway-port 8765
    
    \b
    # Setup and start gateway
    smolclaw setup --hf-token YOUR_TOKEN --start-gateway
    """
    click.echo("=" * 60)
    click.echo("  SmolClaw Setup")
    click.echo("=" * 60)
    
    # Step 1: Create home directory structure
    click.echo("\n[1/5] Creating SmolClaw home directory...")
    home_dir = smolclaw_home_dir()
    ensure_home_layout()
    click.echo(f"  ✓ Created: {home_dir}")
    click.echo(f"  ✓ Workplace: {workplace_dir()}")
    click.echo(f"  ✓ MCP directory: {mcp_dir()}")
    
    # Step 2: Load or create configuration
    click.echo("\n[2/5] Configuring model provider...")
    cfg = load_config()
    
    # Set defaults based on provider
    if provider == "huggingface":
        if not model:
            model = cfg.get("model", HUGGINGFACE_MODELS[0])
        if not base_url:
            base_url = cfg.get("base_url", HUGGINGFACE_BASE_URL)
        if not api_key:
            api_key = cfg.get("api_key", "")
        if not hf_token:
            hf_token = cfg.get("hf_token", "")
        
        click.echo(f"  Provider: Hugging Face")
        click.echo(f"  Model: {model}")
        click.echo(f"  Base URL: {base_url}")
    
    # Step 3: Hugging Face login
    if hf_token:
        click.echo("\n[3/5] Authenticating with Hugging Face...")
        try:
            from huggingface_hub import login
            
            login(token=hf_token, add_to_git_credential=False)
            click.echo("  ✓ Hugging Face login successful")
        except Exception as e:
            click.echo(f"  ⚠ Hugging Face login warning: {e}")
    else:
        click.echo("\n[3/5] Skipping Hugging Face authentication (no token provided)")
    
    # Step 4: Save configuration
    click.echo("\n[4/5] Saving configuration...")
    cfg.update({
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key or "",
        "hf_token": hf_token or "",
        "headless": headless,
        "gateway_host": gateway_host,
        "gateway_port": gateway_port,
    })
    save_config(cfg)
    click.echo(f"  ✓ Configuration saved to: {config_path()}")
    
    if verbose:
        click.echo("\n  Configuration:")
        for key, value in cfg.items():
            if key not in ["api_key", "hf_token"]:
                click.echo(f"    {key}: {value}")
            else:
                click.echo(f"    {key}: {'*' * 8}")
    
    # Step 5: Start gateway if requested
    if start_gateway:
        click.echo("\n[5/5] Starting gateway...")
        pid, started_now = _start_gateway_process(gateway_host, gateway_port)
        if started_now:
            click.echo(f"  ✓ Gateway started (pid={pid})")
            click.echo(f"  ✓ Endpoint: ws://{gateway_host}:{gateway_port}/ws")
        else:
            click.echo(f"  ℹ Gateway already running (pid={pid})")
    else:
        click.echo("\n[5/5] Skipping gateway startup (use 'smolclaw gateway start' to start later)")
    
    # Summary
    click.echo("\n" + "=" * 60)
    click.echo("  Setup Complete!")
    click.echo("=" * 60)
    click.echo("\nNext steps:")
    click.echo("  • Run 'smolclaw tui' to start the interactive assistant")
    click.echo("  • Run 'smolclaw gateway status' to check gateway status")
    click.echo("  • Edit config at: ~/.smolclaw/config/config.json")
    click.echo("")


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


@main.command(help="Start TUI client (connects to gateway).")
@click.option("--url", default="ws://127.0.0.1:8765/ws", help="Gateway WebSocket URL")
@click.option("--session", default="tui", help="Session ID")
def tui(url: str, session: str) -> None:
    """Start TUI client that connects to gateway."""
    from smolclaw.gateway.tui_client import run_tui_sync
    
    run_tui_sync(url, session)


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
