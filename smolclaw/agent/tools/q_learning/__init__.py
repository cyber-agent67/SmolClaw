"""Backward-compat shim — canonical location is smolclaw.cognitive.smolQ."""

from smolclaw.cognitive.smolQ import (
    QLearningScoreEntity,
    QLearningState,
    ScoreTaskProgress,
    score_task_progress_q_learning,
    get_q_state as get_q_learning_state,
    reset_q_state as reset_q_learning_state,
)

__all__ = [
    "QLearningScoreEntity",
    "QLearningState",
    "ScoreTaskProgress",
    "score_task_progress_q_learning",
    "get_q_learning_state",
    "reset_q_learning_state",
]
