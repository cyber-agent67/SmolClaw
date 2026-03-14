"""smolQ scoring — Q-learning computation with cosine-similarity reward."""

from __future__ import annotations

import math
import re
from typing import Dict, Optional

from smolclaw.cognitive.smolQ.entities import QLearningScoreEntity


class ScoreTaskProgress:
    """Scores task progress using Q-learning with vector-similarity reward.

    Reward signal:
        reward = 0.7 * cosine_similarity(task, page) + 0.3 * llm_score

    Q-value update (Bellman equation):
        Q(s) ← Q(s) + α * (r + γ * max(Q) − Q(s))
    """

    @staticmethod
    def _vectorize(text: str) -> Dict[str, float]:
        """Bag-of-words vector from text."""
        vector: Dict[str, float] = {}
        for token in re.findall(r"[a-z0-9]+", (text or "").lower()):
            vector[token] = vector.get(token, 0.0) + 1.0
        return vector

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        """Cosine similarity between two bag-of-words vectors."""
        if not a or not b:
            return 0.0
        dot = sum(v * b.get(k, 0.0) for k, v in a.items())
        mag_a = math.sqrt(sum(v * v for v in a.values()))
        mag_b = math.sqrt(sum(v * v for v in b.values()))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    @staticmethod
    def execute(
        q_values: Dict[str, float],
        visit_counts: Dict[str, int],
        task_prompt: str,
        action_name: str = "observe",
        llm_score: Optional[float] = None,
        alpha: float = 0.5,
        gamma: float = 0.8,
    ) -> QLearningScoreEntity:
        """Compute Q-learning score for the current browser page.

        Args:
            q_values: Mutable Q-value table (updated in-place)
            visit_counts: Mutable visit counter table (updated in-place)
            task_prompt: Natural language task description
            action_name: Name of the action that led to this state
            llm_score: Optional external score from LLM (0–1); falls back to vector_reward
            alpha: Learning rate
            gamma: Discount factor

        Returns:
            QLearningScoreEntity with all computed values
        """
        from smolclaw.tools.smolhand.services import BrowserLayerService

        page_state = BrowserLayerService.current_page_state()
        state_key = page_state["url"]

        task_vec = ScoreTaskProgress._vectorize(task_prompt)
        page_vec = ScoreTaskProgress._vectorize(
            f"{page_state['title']} {page_state['page_source'][:20000]}"
        )
        vector_reward = ScoreTaskProgress._cosine(task_vec, page_vec)
        model_score = float(llm_score) if llm_score is not None else vector_reward

        visit_counts[state_key] = visit_counts.get(state_key, 0) + 1

        old_q = q_values.get(state_key, 0.0)
        future_estimate = max(q_values.values(), default=0.0)
        reward = (0.7 * vector_reward) + (0.3 * model_score)
        updated_q = old_q + alpha * (reward + gamma * future_estimate - old_q)
        q_values[state_key] = updated_q

        return QLearningScoreEntity(
            state=state_key,
            action=action_name,
            task=task_prompt,
            vector_reward=round(vector_reward, 6),
            llm_score=round(model_score, 6),
            reward=round(reward, 6),
            q_value=round(updated_q, 6),
            visits=visit_counts[state_key],
            title=page_state["title"],
        )


__all__ = ["ScoreTaskProgress"]
