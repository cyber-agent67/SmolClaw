"""Shared TF-IDF cosine similarity retrieval for all context layers.

This is the core of the RAG system — given a query, rank a corpus of
(key, text) pairs by relevance and return the top-k.

No external dependencies — uses the same bag-of-words approach as smolQ
so it works in any environment without sentence-transformers.
"""

from __future__ import annotations

import math
import re
from typing import List, Tuple


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _tf(tokens: List[str]) -> dict:
    vec: dict = {}
    for t in tokens:
        vec[t] = vec.get(t, 0.0) + 1.0
    return vec


def _cosine(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0.0) for k, v in a.items())
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def rank(
    query: str,
    corpus: List[Tuple[str, str]],
    top_k: int = 5,
) -> List[Tuple[str, str, float]]:
    """Rank corpus entries by relevance to query.

    Args:
        query: The task or intent text
        corpus: List of (key, text) pairs to rank
        top_k: Number of top results to return

    Returns:
        List of (key, text, score) sorted descending by score
    """
    q_vec = _tf(_tokenize(query))
    scored = []
    for key, text in corpus:
        score = _cosine(q_vec, _tf(_tokenize(text)))
        scored.append((key, text, score))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:top_k]


def estimate_tokens(text: str) -> int:
    """Rough token estimate: 4 chars ≈ 1 token."""
    return max(1, len(text) // 4)


def truncate_to_budget(text: str, token_budget: int) -> str:
    """Truncate text to fit within token budget."""
    char_limit = token_budget * 4
    if len(text) <= char_limit:
        return text
    return text[:char_limit].rsplit(" ", 1)[0] + " ..."


__all__ = ["rank", "estimate_tokens", "truncate_to_budget"]
