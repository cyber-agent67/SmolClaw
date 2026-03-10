"""Configuration helpers for smolclaw CLI and gateway."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def smolclaw_home_dir() -> Path:
    target = Path.home() / ".smolclaw"
    target.mkdir(parents=True, exist_ok=True)
    return target


def workplace_dir() -> Path:
    target = smolclaw_home_dir() / "workplace"
    target.mkdir(parents=True, exist_ok=True)
    return target


def mcp_dir() -> Path:
    target = smolclaw_home_dir() / "mcp"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _load_packaged_template(relative_path: str) -> str:
    try:
        from smolclaw.templates_loader import load_template_text

        return load_template_text(relative_path).strip()
    except Exception:
        return ""


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def ensure_home_layout() -> None:
    root = smolclaw_home_dir()
    (root / "config").mkdir(parents=True, exist_ok=True)
    workplace_dir()
    mcp_dir()

    think_system = _load_packaged_template("prompts/think_system.md")
    smolhand_system = _load_packaged_template("prompts/smolhand_system.md")
    browser_skill = _load_packaged_template("skills/browser/browser_navigation_skill.md")

    soul_content = "# SOUL\n\n"
    if think_system:
        soul_content += think_system + "\n"
    else:
        soul_content += "Define your persistent operating principles for SmolClaw here.\n"

    tools_content = "# TOOLS\n\n"
    if smolhand_system:
        tools_content += smolhand_system + "\n"
    else:
        tools_content += "List available tools and their expected JSON signatures here.\n"

    skills_content = "# SKILLS\n\n"
    if browser_skill:
        skills_content += browser_skill + "\n"
    else:
        skills_content += "Document reusable skills and when the agent should invoke them.\n"

    _write_if_missing(root / "SOUL.md", soul_content)
    _write_if_missing(root / "TOOLS.md", tools_content)
    _write_if_missing(root / "TOOS.md", tools_content)
    _write_if_missing(root / "SKILLS.md", skills_content)


def config_dir() -> Path:
    ensure_home_layout()
    target = smolclaw_home_dir() / "config"
    target.mkdir(parents=True, exist_ok=True)
    return target


def config_path() -> Path:
    return config_dir() / "config.json"


def pid_path() -> Path:
    return config_dir() / "gateway.pid"


def log_path() -> Path:
    return config_dir() / "gateway.log"


def load_config() -> Dict[str, Any]:
    cfg_file = config_path()
    if not cfg_file.exists():
        return {}
    try:
        return json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data: Dict[str, Any]) -> None:
    config_path().write_text(json.dumps(data, indent=2), encoding="utf-8")
