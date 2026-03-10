"""Interactions for Layer 4 (Q-learning task scoring)."""

from __future__ import annotations

import math
import re
from typing import Dict

from browser_subagents.layers.layer1_browser.interactions import ReadCurrentPage
from browser_subagents.layers.layer4_q_learning.entities import QLearningScoreEntity


class ScoreTaskProgress:
    @staticmethod
    def _vectorize(text: str) -> Dict[str, float]:
        vector: Dict[str, float] = {}
        for token in re.findall(r"[a-z0-9]+", (text or "").lower()):
            vector[token] = vector.get(token, 0.0) + 1.0
        return vector

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
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
        llm_score: float | None = None,
        alpha: float = 0.5,
        gamma: float = 0.8,
    ) -> QLearningScoreEntity:
        page = ReadCurrentPage.execute()
        state_key = page.url

        task_vector = ScoreTaskProgress._vectorize(task_prompt)
        page_vector = ScoreTaskProgress._vectorize(f"{page.title} {page.page_source[:20000]}")
        vector_reward = ScoreTaskProgress._cosine(task_vector, page_vector)
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
            title=page.title,
        )
