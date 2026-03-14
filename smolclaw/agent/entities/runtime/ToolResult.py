"""ToolResult entity - result from tool execution."""

from typing import Any, Optional


class ToolResult:
    def __init__(self):
        self.tool_name: str = ""
        self.success: bool = False
        self.result: Any = None
        self.error: Optional[str] = None
        self.execution_time: float = 0.0
