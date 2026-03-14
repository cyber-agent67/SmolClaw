"""Exploration tool for AI Agent A* DOM link ranking.

This module provides the @tool decorated function that exposes A* heuristic
exploration to the AI Agent.
"""

import json
from typing import Dict, Optional

from smolagents import tool


@tool
def explore_dom_with_astar(
    target: str,
    keyword_values: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """Use A* heuristics to rank hyperlinks on the current page by relevance.

    This tool analyzes all links on the current page and ranks them using:
    - Keyword matching with the target description
    - A* heuristic scoring for navigation decisions
    - Optional keyword weights for fine-tuning

    Args:
        target: Natural language description of what you're looking for
            (e.g., "release notes", "download page", "settings")
        keyword_values: Optional JSON string with keyword weights
            Example: '{"release": 18, "version": 8, "download": 12}'
        top_k: Number of top links to return (default: 5)

    Returns:
        JSON string with exploration results including:
        - target: The target description
        - strategy: Exploration strategy ("a_star")
        - current_url: Current page URL
        - title: Current page title
        - ranked_links: List of top-k links with href, text, title, and score

    Example:
        explore_dom_with_astar("Find the latest release notes")
        explore_dom_with_astar("Download page", keyword_values='{"download": 20}')
    """
    from smolclaw.agent.tools.exploration.interactions import ExploreCurrentPageAStar

    # Parse keyword weights if provided
    keyword_weights = {}
    if keyword_values:
        try:
            keyword_weights = json.loads(keyword_values)
        except Exception:
            keyword_weights = {}

    result = ExploreCurrentPageAStar.execute(
        target=target,
        keyword_weights=keyword_weights,
        top_k=top_k,
    )
    return json.dumps(result.as_dict(), indent=2)


__all__ = ["explore_dom_with_astar"]
