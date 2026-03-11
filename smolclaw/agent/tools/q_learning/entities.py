"""Q-learning state entities for navigation scoring.

This module provides state containers for Q-learning based task progress scoring.
The Q-learning tool is used by the AI Agent to evaluate navigation decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class QLearningScoreEntity:
    """Represents Q-learning score for a state-action pair during task execution.

    Attributes:
        state: Current page URL (state identifier)
        action: Action name being scored
        task: Task prompt/description
        vector_reward: Cosine similarity between task and page vectors
        llm_score: Optional LLM-provided score
        reward: Combined reward (0.7 * vector + 0.3 * llm)
        q_value: Updated Q-value for this state
        visits: Number of times this state has been visited
        title: Current page title
    """
    state: str
    action: str
    task: str
    vector_reward: float
    llm_score: float
    reward: float
    q_value: float
    visits: int
    title: str

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "state": self.state,
            "action": self.action,
            "task": self.task,
            "vector_reward": self.vector_reward,
            "llm_score": self.llm_score,
            "reward": self.reward,
            "q_value": self.q_value,
            "visits": self.visits,
            "title": self.title,
        }


@dataclass
class QLearningState:
    """Represents the full Q-learning state table for navigation.

    This is the stateful component that tracks Q-values and visit counts
    across all visited pages during a navigation session.

    Attributes:
        q_values: Dictionary mapping state keys to Q-values
        visit_counts: Dictionary mapping state keys to visit counts
        task_prompt: Current task being executed
    """
    q_values: Dict[str, float]
    visit_counts: Dict[str, int]
    task_prompt: str = ""

    def get_state_key(self, url: str) -> str:
        """Get normalized state key for a URL."""
        return url

    def reset(self) -> None:
        """Reset all Q-values and visit counts."""
        self.q_values.clear()
        self.visit_counts.clear()


__all__ = ["QLearningScoreEntity", "QLearningState"]
