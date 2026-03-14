"""Backward-compat shim — canonical location is smolclaw.cognitive.smolQ.tool."""

from smolclaw.cognitive.smolQ.tool import (
    score_task_progress_q_learning,
    get_q_state as get_q_learning_state,
    reset_q_state as reset_q_learning_state,
)

__all__ = ["score_task_progress_q_learning", "get_q_learning_state", "reset_q_learning_state"]
