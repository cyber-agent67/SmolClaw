"""Tool registry — ToolRegistry class and SmolhandTools adapter."""

from typing import Any, Callable, Dict

from tools.builtin.browser import all_browser_tools, _tool_name, get_navigation_stack


class ToolRegistry:
    """Central registry for all available tools."""

    @staticmethod
    def get_all_tools():
        """Returns all registered tools for the agent."""
        return all_browser_tools()

    @staticmethod
    def get_tool_names():
        """Returns names of all registered tools."""
        return [_tool_name(t) for t in all_browser_tools()]


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
