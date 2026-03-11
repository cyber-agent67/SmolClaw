"""Vision tool for AI Agent visual page analysis.

This module provides the @tool decorated function that exposes Florence-2
vision analysis to the AI Agent.
"""

import json

from smolagents import tool


@tool
def analyze_visual_context(prompt_hint: str = "") -> str:
    """Use Florence-2 vision AI to analyze the current page's visual content.

    This tool captures a screenshot and uses Florence-2 to generate:
    - Brief visual caption
    - Detailed visual description
    - Region detection and descriptions

    Args:
        prompt_hint: Optional hint to guide the visual analysis
            (e.g., "Find the settings menu", "What buttons are visible?")

    Returns:
        JSON string with visual analysis results including:
        - prompt_hint: The hint provided
        - url: Current page URL
        - title: Current page title
        - florence_status: Model loading status
        - visual_caption: Brief visual description
        - visual_detail: Detailed visual description
        - regions: List of detected regions with descriptions

    Example:
        analyze_visual_context("Find the login button")
        analyze_visual_context("What settings are visible?")
    """
    from smolclaw.agent.tools.vision.interactions import BuildVisionContext

    context = BuildVisionContext.execute(prompt_hint)
    return json.dumps(context.as_dict(), indent=2)


__all__ = ["analyze_visual_context"]
