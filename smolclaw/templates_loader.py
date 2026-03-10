"""Template loading utilities for markdown-based prompts and skills."""

from __future__ import annotations

from importlib import resources
from typing import Mapping


def load_template_text(relative_path: str) -> str:
    """Loads a template file from smolclaw/templates by relative path."""
    base = resources.files("smolclaw").joinpath("templates")
    target = base.joinpath(relative_path)
    return target.read_text(encoding="utf-8")


def render_template(relative_path: str, values: Mapping[str, object] | None = None) -> str:
    """Loads and renders a simple {{key}} placeholder template."""
    text = load_template_text(relative_path)
    if not values:
        return text

    rendered = text
    for key, value in values.items():
        rendered = rendered.replace("{{" + str(key) + "}}", str(value))
    return rendered
