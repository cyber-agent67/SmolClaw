"""smolclaw-local agentic runner entrypoint."""

import json
import logging

from smolclaw.agent.main import cleanup_resources, run_agent_with_args
from smolclaw.config import load_tool_prompts

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool prompt loading
# ---------------------------------------------------------------------------

_TOOL_PROMPT_SECTIONS = {
    "browser": "Browser Tool",
    "q_learning": "Q-Learning Tool",
}


def _load_tool_instruction_block() -> str:
    """Load Prompts.json for each registered tool and format as a system-prompt section."""
    sections: list[str] = []
    for tool_key, heading in _TOOL_PROMPT_SECTIONS.items():
        prompts = load_tool_prompts(tool_key)
        if prompts:
            sections.append(f"### {heading}\n{json.dumps(prompts, indent=2)}")

    if not sections:
        return ""
    return "## Available Tools\n\n" + "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Tool registration helpers
# ---------------------------------------------------------------------------


def _register_core_tools():
    """Import and return the browser and score_progress smolagents tools."""
    from tools.browser_tool import browser
    from tools.q_learning_tool import score_progress
    return [browser, score_progress]


def get_agent_tools():
    """Return the full list of tools for the SmolClaw agent.

    Merges the core browser/q_learning tools with any tools already provided
    by the agentic_navigator ToolRegistry (which includes think, final_answer,
    web_search, etc.).
    """
    core_tools = _register_core_tools()

    try:
        from smolclaw.agent.tools.ToolRegistry import ToolRegistry
        registry_tools = ToolRegistry.get_all_tools()
    except Exception:
        registry_tools = []

    # Deduplicate by tool name — core tools take priority.
    seen_names: set[str] = set()
    merged: list = []
    for t in core_tools:
        name = getattr(t, "name", None) or getattr(t, "__name__", "")
        if name not in seen_names:
            seen_names.add(name)
            merged.append(t)
    for t in registry_tools:
        name = getattr(t, "name", None) or getattr(t, "__name__", "")
        if name not in seen_names:
            seen_names.add(name)
            merged.append(t)

    return merged


def get_tool_instructions() -> str:
    """Public helper so callers can obtain the formatted tool-instruction block."""
    return _load_tool_instruction_block()


__all__ = [
    "run_agent_with_args",
    "cleanup_resources",
    "get_agent_tools",
    "get_tool_instructions",
    "load_tool_prompts",
]