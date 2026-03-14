"""smolQ — Q-learning navigation intelligence for the cognitive system.

smolQ provides reinforcement learning-based page scoring that helps the
agent learn optimal navigation paths toward a task goal.

Core concepts:
- State: current page URL
- Action: navigation action taken (click, navigate, observe)
- Reward: cosine similarity between task vector and page content
- Q-value: learned long-term value of a (state, action) pair

Usage:
    from smolclaw.cognitive.smolQ import score_task_progress_q_learning

    # As an agent @tool
    result_json = score_task_progress_q_learning("Find device registration docs")

    # Programmatic access
    from smolclaw.cognitive.smolQ import ScoreTaskProgress, QLearningState
    state = QLearningState(q_values={}, visit_counts={})
    score = ScoreTaskProgress.execute(state.q_values, state.visit_counts, "my task")
"""

from smolclaw.cognitive.smolQ.entities import QLearningScoreEntity, QLearningState
from smolclaw.cognitive.smolQ.scoring import ScoreTaskProgress
from smolclaw.cognitive.smolQ.tool import (
    get_q_state,
    reset_q_state,
    score_task_progress_q_learning,
)

__all__ = [
    "QLearningScoreEntity",
    "QLearningState",
    "ScoreTaskProgress",
    "score_task_progress_q_learning",
    "get_q_state",
    "reset_q_state",
]
