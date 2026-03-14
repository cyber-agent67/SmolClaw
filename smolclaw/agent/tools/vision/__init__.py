"""Vision tools for AI Agent visual page analysis.

This package provides Florence-2 vision analysis as a tool for the AI Agent.
"""

from smolclaw.agent.tools.vision.entities import VisionContextEntity
from smolclaw.agent.tools.vision.interactions import BuildVisionContext
from smolclaw.agent.tools.vision.tool import analyze_visual_context

__all__ = [
    # Entities
    "VisionContextEntity",
    # Interactions
    "BuildVisionContext",
    # Tool
    "analyze_visual_context",
]
