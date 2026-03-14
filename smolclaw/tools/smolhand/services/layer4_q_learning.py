"""Service facade for Layer 4 (Q-learning task scoring).

Note: Q-learning is now in smolclaw.agent.tools.q_learning as a tool.
This is a stub for compatibility.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


class QLearningLayerService:
    """Service facade for Layer 4 Q-learning."""

    def __init__(self):
        self.q_values: Dict[str, float] = {}
        self.visit_counts: Dict[str, int] = {}

    def score_current_page(
        self,
        task_prompt: str,
        action_name: str = "observe",
        llm_score: Optional[float] = None,
        alpha: float = 0.5,
        gamma: float = 0.8,
    ) -> Dict[str, Any]:
        """Score current page."""
        return {
            "task": task_prompt,
            "action": action_name,
            "note": "Use smolclaw.agent.tools.q_learning for full Q-learning",
            "q_value": 0.0,
        }

    def score_current_page_json(
        self,
        task_prompt: str,
        action_name: str = "observe",
        llm_score: Optional[float] = None,
        alpha: float = 0.5,
        gamma: float = 0.8,
    ) -> str:
        """Score and return JSON."""
        return json.dumps(
            self.score_current_page(task_prompt, action_name, llm_score, alpha, gamma),
            indent=2,
        )


__all__ = ["QLearningLayerService"]
