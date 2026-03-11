"""smolclaw package."""

__all__ = [
    "cleanup_resources",
    "run_agent_with_args",
    "OpenAICompatClient",
    "SmolhandRunner",
    "ToolDefinition",
    "default_tools",
    "tools",  # Tool packages (smolhand, smoleyes)
]


def __getattr__(name):
    if name in {"cleanup_resources", "run_agent_with_args"}:
        from smolclaw.agentic_runner import cleanup_resources, run_agent_with_args

        return {
            "cleanup_resources": cleanup_resources,
            "run_agent_with_args": run_agent_with_args,
        }[name]

    if name in {"OpenAICompatClient", "SmolhandRunner", "ToolDefinition", "default_tools"}:
        from smolclaw.tool_calling import OpenAICompatClient, SmolhandRunner, ToolDefinition, default_tools

        return {
            "OpenAICompatClient": OpenAICompatClient,
            "SmolhandRunner": SmolhandRunner,
            "ToolDefinition": ToolDefinition,
            "default_tools": default_tools,
        }[name]

    if name == "tools":
        import smolclaw.tools

        return smolclaw.tools

    raise AttributeError(name)
