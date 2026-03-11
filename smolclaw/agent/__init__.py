"""AI Agent core for SmolClaw.

This package provides the core AI Agent navigation logic using the Entity-Interaction Model (EIM).

Structure:
- entities: State containers (Browser, Tab, NavigationStack, etc.)
- interactions: Business logic (navigation, tabs, browser, agent, etc.)
- tools: AI Agent tools (Vision, Exploration, Q-Learning, Browser tools)
- repositories: Persistence (cache, experience, navigation stack)
- config: Configuration (BrowserConfig)
- main: Agent orchestration (run_agent_with_args)
"""

from smolclaw.agent.main import cleanup_resources, run_agent_with_args

__all__ = ["run_agent_with_args", "cleanup_resources"]
