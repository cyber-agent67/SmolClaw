"""Execute one imperative command using tool registry map."""

from agentic_navigator.entities.runtime.ToolResult import ToolResult


class ExecuteCommand:
    @staticmethod
    def execute(tool_name: str, arguments: dict, tool_map: dict) -> ToolResult:
        result = ToolResult()
        result.tool_name = tool_name

        if tool_name not in tool_map:
            result.success = False
            result.error = f"Unknown tool: {tool_name}"
            return result

        try:
            result.result = tool_map[tool_name](**arguments)
            result.success = True
        except Exception as e:
            result.success = False
            result.error = str(e)
        return result
