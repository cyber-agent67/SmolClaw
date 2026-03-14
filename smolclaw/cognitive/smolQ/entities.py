"""smolQ entities — state containers for Q-learning navigation scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class QLearningScoreEntity:
    """Result of a single Q-learning scoring step.

    Attributes:
        state: Current page URL (state identifier)
        action: Navigation action taken
        task: Task description used for vector similarity
        vector_reward: Cosine similarity between task and page content (0–1)
        llm_score: Optional LLM-provided score, falls back to vector_reward
        reward: Combined reward (0.7 * vector_reward + 0.3 * llm_score)
        q_value: Updated Q-value for this state after learning step
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
    """Full Q-learning state table for a navigation session.

    Tracks Q-values and visit counts across all pages visited.
    Reset at the start of each new task.

    Attributes:
        q_values: Maps state key (URL) → learned Q-value
        visit_counts: Maps state key (URL) → number of visits
        task_prompt: Current task being executed
    """
    q_values: Dict[str, float] = field(default_factory=dict)
    visit_counts: Dict[str, int] = field(default_factory=dict)
    task_prompt: str = ""

    def reset(self) -> None:
        """Reset all Q-values and visit counts for a new session."""
        self.q_values.clear()
        self.visit_counts.clear()
        self.task_prompt = ""


__all__ = ["QLearningScoreEntity", "QLearningState"]
