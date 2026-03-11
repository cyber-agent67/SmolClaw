"""smolclaw tools package.

This package contains tool integrations:
- smolhand: Browser automation + Small LLM runtime
- smoleyes: Vision-based browser analysis (Florence-2)
"""

from smolclaw.agent.tools.SmolhandTools import SmolhandTools
from smolclaw.agent.tools.ToolRegistry import ToolRegistry
from smolclaw.tools import smolhand, smoleyes

__all__ = ["SmolhandTools", "ToolRegistry", "smolhand", "smoleyes"]