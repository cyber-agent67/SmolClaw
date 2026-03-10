"""Initialize agent interaction."""

from smolagents import CodeAgent
from smolagents.cli import load_model

from agentic_navigator.entities.runtime.Agent import Agent
from agentic_navigator.tools.ToolRegistry import ToolRegistry


class InitializeAgent:
    @staticmethod
    def execute(model_type: str, model_id: str, screenshot_callback: callable) -> Agent:
        """Initializes the CodeAgent with model and tools."""
        agent_entity = Agent()
        agent_entity.model = load_model(model_type, model_id)

        tools = ToolRegistry.get_all_tools()
        agent_entity.code_agent = CodeAgent(
            tools=tools,
            model=agent_entity.model,
            additional_authorized_imports=["helium"],
            step_callbacks=[screenshot_callback],
            max_steps=agent_entity.max_steps,
            verbosity_level=agent_entity.verbosity_level,
        )

        return agent_entity
