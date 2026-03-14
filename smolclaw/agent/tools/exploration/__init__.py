"""Exploration tools for AI Agent A* DOM link ranking.

This package provides A* heuristic exploration as a tool for the AI Agent.
"""

from smolclaw.agent.tools.exploration.entities import ExplorationResultEntity, RankedLinkEntity
from smolclaw.agent.tools.exploration.interactions import ExploreCurrentPageAStar
from smolclaw.agent.tools.exploration.tool import explore_dom_with_astar

__all__ = [
    # Entities
    "RankedLinkEntity",
    "ExplorationResultEntity",
    # Interactions
    "ExploreCurrentPageAStar",
    # Tool
    "explore_dom_with_astar",
]
