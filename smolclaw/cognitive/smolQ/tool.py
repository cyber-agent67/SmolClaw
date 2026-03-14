"""smolQ agent tool — @tool wrapper exposing Q-learning to the agent."""

import json
from typing import Dict, Optional

from smolagents import tool

# Session-scoped Q-learning state (shared across tool calls in one session)
_q_values: Dict[str, float] = {}
_visit_counts: Dict[str, int] = {}
_current_task: str = ""


@tool
def score_task_progress_q_learning(
    task_prompt: str,
    llm_score: Optional[float] = None,
    action_name: str = "observe",
) -> str:
    """Score current page progress toward task completion using Q-learning.

    Uses cosine similarity between the task description and page content as the
    primary reward signal, combined with an optional LLM-provided score.
    Q-values are updated via the Bellman equation across the navigation session.

    Args:
        task_prompt: Natural language description of the task
        llm_score: Optional score from LLM evaluation (0.0–1.0)
        action_name: Name of the action that led to the current page

    Returns:
        JSON string with:
          state, action, task, vector_reward, llm_score, reward, q_value, visits, title
    """
    from smolclaw.cognitive.smolQ.scoring import ScoreTaskProgress

    global _q_values, _visit_counts, _current_task

    if task_prompt:
        _current_task = task_prompt

    score = ScoreTaskProgress.execute(
        q_values=_q_values,
        visit_counts=_visit_counts,
        task_prompt=task_prompt,
        action_name=action_name,
        llm_score=llm_score,
    )

    return json.dumps(score.as_dict(), indent=2)


def get_q_state() -> Dict:
    """Return the current session Q-learning state table."""
    return {
        "q_values": dict(_q_values),
        "visit_counts": dict(_visit_counts),
        "current_task": _current_task,
    }


def reset_q_state() -> None:
    """Reset Q-learning state for a new navigation session."""
    global _q_values, _visit_counts, _current_task
    _q_values.clear()
    _visit_counts.clear()
    _current_task = ""


__all__ = ["score_task_progress_q_learning", "get_q_state", "reset_q_state"]
