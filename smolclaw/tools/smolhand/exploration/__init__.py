"""Exploration-focused browser sub-agents.

Deprecated: HeuristicExplorer has been moved to browser_subagents.scoring.
This module re-exports for backward compatibility.
"""

from smolclaw.tools.smolhand.scoring.heuristic_scorer import HeuristicScorer as HeuristicExplorer

__all__ = ["HeuristicExplorer"]