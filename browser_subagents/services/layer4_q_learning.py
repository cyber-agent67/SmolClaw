"""Service facade for Layer 4 (Q-learning task scoring)."""

from __future__ import annotations

import json
from typing import Any, Dict

from browser_subagents.layers.layer4_q_learning.interactions import ScoreTaskProgress


class QLearningLayerService:
	def __init__(self):
		self.q_values: Dict[str, float] = {}
		self.visit_counts: Dict[str, int] = {}

	def score_current_page(
		self,
		task_prompt: str,
		action_name: str = "observe",
		llm_score: float | None = None,
		alpha: float = 0.5,
		gamma: float = 0.8,
	) -> Dict[str, Any]:
		score = ScoreTaskProgress.execute(
			q_values=self.q_values,
			visit_counts=self.visit_counts,
			task_prompt=task_prompt,
			action_name=action_name,
			llm_score=llm_score,
			alpha=alpha,
			gamma=gamma,
		)
		return score.as_dict()

	def score_current_page_json(
		self,
		task_prompt: str,
		action_name: str = "observe",
		llm_score: float | None = None,
		alpha: float = 0.5,
		gamma: float = 0.8,
	) -> str:
		payload = self.score_current_page(task_prompt, action_name=action_name, llm_score=llm_score, alpha=alpha, gamma=gamma)
		return json.dumps(payload, indent=2)
__all__ = ["QLearningLayerService"]
