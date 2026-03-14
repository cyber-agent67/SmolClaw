"""Q-learning tool for AI Agent navigation scoring.

This module provides the @tool decorated function that exposes Q-learning
state tracking and scoring to the AI Agent.
"""

import json
from typing import Dict, Optional

from smolagents import tool

# Global Q-learning state (shared across tool calls in a session)
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

    This tool tracks navigation states and computes rewards based on:
    - Vector similarity between task and page content
    - Optional LLM-provided scores
    - Q-value updates for learning optimal navigation paths

    Args:
        task_prompt: Natural language description of the task
        llm_score: Optional score from LLM evaluation (0.0-1.0)
        action_name: Name of the action that led to this state

    Returns:
        JSON string with scoring results including:
        - state: Current page URL
        - action: Action name
        - task: Task prompt
        - vector_reward: Task/page similarity (0.0-1.0)
        - llm_score: LLM score or vector reward
        - reward: Combined reward
        - q_value: Updated Q-value for this state
        - visits: Number of visits to this state
        - title: Current page title

    Example:
        score_task_progress_q_learning(
            "Find the latest release notes",
            llm_score=0.8,
            action_name="click_link"
        )
    """
    from smolclaw.agent.tools.q_learning.interactions import ScoreTaskProgress

    global _q_values, _visit_counts, _current_task

    # Update current task if provided
    if task_prompt:
        _current_task = task_prompt

    # Execute scoring
    score = ScoreTaskProgress.execute(
        q_values=_q_values,
        visit_counts=_visit_counts,
        task_prompt=task_prompt,
        action_name=action_name,
        llm_score=llm_score,
    )

    # Return as JSON string
    return json.dumps(score.as_dict(), indent=2)


def get_q_learning_state() -> Dict:
    """Get current Q-learning state table.

    Returns:
        Dictionary with q_values, visit_counts, and current_task
    """
    return {
        "q_values": dict(_q_values),
        "visit_counts": dict(_visit_counts),
        "current_task": _current_task,
    }


def reset_q_learning_state() -> None:
    """Reset Q-learning state table for new navigation session."""
    global _q_values, _visit_counts, _current_task
    _q_values.clear()
    _visit_counts.clear()
    _current_task = ""


__all__ = [
    "score_task_progress_q_learning",
    "get_q_learning_state",
    "reset_q_learning_state",
]
