"""Q-learning scoring operations for navigation decisions.

This module provides the Q-learning computation logic used by the AI Agent
to score task progress and update Q-values for navigation states.
"""

from __future__ import annotations

import math
import re
from typing import Dict, Optional

from smolclaw.agent.tools.q_learning.entities import QLearningScoreEntity


class ScoreTaskProgress:
    """Scores task progress using Q-learning with vector similarity reward.

    This is a stateless operation class that computes Q-learning scores
    based on the current state, action, and task context.
    """

    @staticmethod
    def _vectorize(text: str) -> Dict[str, float]:
        """Convert text to bag-of-words vector representation.

        Args:
            text: Text to vectorize

        Returns:
            Dictionary mapping tokens to frequencies
        """
        vector: Dict[str, float] = {}
        for token in re.findall(r"[a-z0-9]+", (text or "").lower()):
            vector[token] = vector.get(token, 0.0) + 1.0
        return vector

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            a: First vector
            b: Second vector

        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        if not a or not b:
            return 0.0
        dot = 0.0
        for token, value in a.items():
            dot += value * b.get(token, 0.0)
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
        """
        Execute Q-learning score computation for current page state.

        Args:
            q_values: Dictionary of Q-values for state-action pairs
            visit_counts: Dictionary of visit counts per state
            task_prompt: The task description for vector similarity
            action_name: Name of the action being scored
            llm_score: Optional LLM-provided score (defaults to vector reward)
            alpha: Learning rate for Q-value updates
            gamma: Discount factor for future rewards

        Returns:
            QLearningScoreEntity with computed scores and updated Q-value
        """
        # Get current page state
        from smolclaw.smolhand.services import BrowserLayerService

        page_state = BrowserLayerService.current_page_state()
        state_key = page_state["url"]

        # Compute vector similarity reward
        task_vector = ScoreTaskProgress._vectorize(task_prompt)
        page_vector = ScoreTaskProgress._vectorize(
            f"{page_state['title']} {page_state['page_source'][:20000]}"
        )
        vector_reward = ScoreTaskProgress._cosine(task_vector, page_vector)
        model_score = float(llm_score) if llm_score is not None else vector_reward

        # Update visit count
        visit_counts[state_key] = visit_counts.get(state_key, 0) + 1

        # Q-learning update
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
