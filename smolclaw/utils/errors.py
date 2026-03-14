"""Custom exception hierarchy for SmolClaw."""


class SmolClawError(Exception):
    """Base exception for all SmolClaw errors."""


class ChannelError(SmolClawError):
    """Channel connection or communication failure."""


class ProviderError(SmolClawError):
    """LLM provider API failure."""


class ToolExecutionError(SmolClawError):
    """Tool execution failed."""

    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {reason}")


class ContextOverflowError(SmolClawError):
    """Context window exceeded."""


class ConfigError(SmolClawError):
    """Invalid or missing configuration."""


class BrowserError(SmolClawError):
    """Browser automation failure."""


class MemoryError(SmolClawError):
    """Memory store read/write failure."""


class GatewayError(SmolClawError):
    """WebSocket gateway error."""
