"""smolclaw package - Distributed Cognitive System."""

__all__ = [
    "cleanup_resources",
    "run_agent_with_args",
    "OpenAICompatClient",
    "SmolhandRunner",
    "ToolDefinition",
    "default_tools",
    "tools",  # Tool packages (smolhand, smoleyes)
    "cognitive",  # Cognitive system core
    "CognitiveLoop",  # Cognitive runloop
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

    if name == "cognitive":
        import smolclaw.cognitive

        return smolclaw.cognitive

    if name == "CognitiveLoop":
        from smolclaw.cognitive_loop import CognitiveLoop

        return CognitiveLoop

    raise AttributeError(name)
