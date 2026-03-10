"""smolhand tools adapter for EIM interactions."""

from typing import Any, Callable, Dict

from agentic_navigator.tools.ToolRegistry import ToolRegistry


class SmolhandTools:
    @staticmethod
    def as_name_map() -> Dict[str, Callable[..., Any]]:
        tools = ToolRegistry.get_all_tools()
        mapping: Dict[str, Callable[..., Any]] = {}
        for tool in tools:
            name = getattr(tool, "name", None) or getattr(tool, "__name__", None)
            if name:
                mapping[name] = tool
        return mapping
