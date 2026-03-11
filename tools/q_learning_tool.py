"""Q-Learning task progress scoring tool for SmolAgent.

Measures how close the current page is to completing a task by computing
cosine similarity between the task description and page content.
"""

from __future__ import annotations

import json
import logging
from math import sqrt
from typing import Any, Dict

from smolagents import tool

logger = logging.getLogger(__name__)

# Module-level state (shared across calls within a session)
_q_values: Dict[str, float] = {}
_visit_counts: Dict[str, int] = {}

# Module-level browser reference
_browser = None


def set_browser(browser_instance) -> None:
    """Set the browser reference for page state access."""
    global _browser
    _browser = browser_instance


def reset_state() -> None:
    """Reset Q-values and visit counts (e.g., for a new task)."""
    global _q_values, _visit_counts
    _q_values = {}
    _visit_counts = {}


def _tokenize(text: str) -> Dict[str, float]:
    """Tokenize text into term frequency vector."""
    tokens: Dict[str, float] = {}
    for word in text.lower().split():
        word = word.strip(".,;:!?()[]{}\"'")
        if len(word) > 1:
            tokens[word] = tokens.get(word, 0.0) + 1.0
    return tokens


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Compute cosine similarity between two term frequency vectors."""
    if not a or not b:
        return 0.0
    dot = sum(a[token] * b.get(token, 0.0) for token in a)
    mag_a = sqrt(sum(v * v for v in a.values()))
    mag_b = sqrt(sum(v * v for v in b.values()))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


@tool
def score_progress(task_prompt: str, action_name: str = "observe",
                   llm_score: float = -1.0) -> str:
    """Q-Learning task progress scorer. Measures how close the current page
    is to completing your task.

    Args:
        task_prompt: Description of the task you are trying to complete.
        action_name: The action that led to this state (default: 'observe').
        llm_score: Your own confidence score 0.0-1.0, or -1 to skip.

    Returns:
        JSON with state, reward, q_value, visits, vector_reward, title.
        High reward (>0.5) = on track. Low reward (<0.2) = try different path.
    """
    global _q_values, _visit_counts

    if _browser is None:
        return json.dumps({"error": "Browser not initialized for Q-learning scoring"})

    try:
        # Get page state
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                url = loop.run_until_complete(_browser.get_current_url())
                title = loop.run_until_complete(_browser.get_page_title())
                source = loop.run_until_complete(_browser.get_page_source())
            else:
                url = loop.run_until_complete(_browser.get_current_url())
                title = loop.run_until_complete(_browser.get_page_title())
                source = loop.run_until_complete(_browser.get_page_source())
        except RuntimeError:
            url = asyncio.run(_browser.get_current_url())
            title = asyncio.run(_browser.get_page_title())
            source = asyncio.run(_browser.get_page_source())

        state_key = url

        # Compute vector reward (cosine similarity)
        task_vector = _tokenize(task_prompt)
        page_text = title + " " + source[:20000]
        page_vector = _tokenize(page_text)
        vector_reward = _cosine(task_vector, page_vector)

        # Combined reward
        model_score = llm_score if llm_score >= 0.0 else vector_reward
        reward = (0.7 * vector_reward) + (0.3 * model_score)

        # Q-value update
        alpha = 0.5
        gamma = 0.8
        _visit_counts[state_key] = _visit_counts.get(state_key, 0) + 1
        old_q = _q_values.get(state_key, 0.0)
        future_estimate = max(_q_values.values(), default=0.0)
        updated_q = old_q + alpha * (reward + gamma * future_estimate - old_q)
        _q_values[state_key] = updated_q

        result = {
            "state": state_key,
            "action": action_name,
            "task": task_prompt[:100],
            "vector_reward": round(vector_reward, 4),
            "llm_score": round(model_score, 4),
            "reward": round(reward, 4),
            "q_value": round(updated_q, 4),
            "visits": _visit_counts[state_key],
            "title": title,
        }
        return json.dumps(result)

    except Exception as e:
        logger.error("Q-learning scoring error: %s", str(e))
        return json.dumps({"error": str(e)})
