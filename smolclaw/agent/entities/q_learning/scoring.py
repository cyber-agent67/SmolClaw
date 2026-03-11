"""Q-Learning task scoring entity."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class QLearningScoreEntity:
    """Result of Q-learning task progress scoring."""

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
