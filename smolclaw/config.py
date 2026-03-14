"""Configuration helpers for smolclaw CLI and gateway."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

# Hugging Face configuration defaults
HUGGINGFACE_BASE_URL = "https://router.huggingface.co/v1"
HUGGINGFACE_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "meta-llama/Llama-3.1-8B-Instruct",
    "HuggingFaceTB/SmolLM3-3B",
]


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


def load_tool_prompts(tool_name: str) -> Dict[str, Any]:
    """Load Prompts.json for a tool. User override takes priority over packaged default."""
    user_file = smolclaw_home_dir() / tool_name / "Prompts.json"
    if user_file.exists():
        try:
            return json.loads(user_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Fallback to packaged template
    default = _load_packaged_template(f"{tool_name}/Prompts.json")
    if default:
        try:
            return json.loads(default)
        except Exception:
            pass
    return {}


def _seed_tool_prompts(root: Path) -> None:
    """Seed Prompts.json files for each tool into ~/.smolclaw/{tool}/."""
    for tool in ["browser", "q_learning"]:
        tool_dir = root / tool
        tool_dir.mkdir(parents=True, exist_ok=True)
        prompts_file = tool_dir / "Prompts.json"
        if not prompts_file.exists():
            default = _load_packaged_template(f"{tool}/Prompts.json")
            if default:
                prompts_file.write_text(default, encoding="utf-8")


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

    # Seed tool Prompts.json files
    _seed_tool_prompts(root)


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
