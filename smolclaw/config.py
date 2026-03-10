"""Configuration helpers for smolclaw CLI and gateway."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        root = Path(base)
    else:
        root = Path.home() / ".config"
    target = root / "smolclaw"
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
