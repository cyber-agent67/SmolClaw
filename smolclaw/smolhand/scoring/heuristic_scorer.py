"""Heuristic scorer with Q-learning/A* style scoring for page navigation.

This module provides the core scoring engine used by Layer 3 (DOM exploration)
and Layer 4 (Q-learning navigation) for ranking links and scoring page content.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


class HeuristicScorer:
    """Ranks links and pages using weighted keyword signals and strategy-specific heuristics.

    Supports two scoring strategies:
    - q_learning: Exploration bonus + target bonus - revisit penalty
    - a_star: Goal bonus - depth penalty

    Attributes:
        strategy: Scoring strategy ("q_learning" or "a_star")
    """

    def __init__(self, strategy: str = "q_learning") -> None:
        """Initialize the heuristic scorer.

        Args:
            strategy: Scoring strategy to use ("q_learning" or "a_star")
        """
        selected = (strategy or "q_learning").strip().lower()
        self.strategy = selected if selected in {"q_learning", "a_star"} else "q_learning"

    @staticmethod
    def _normalize_weights(keyword_weights: Optional[Dict[str, float]]) -> Dict[str, float]:
        """Normalize and validate keyword weights.

        Args:
            keyword_weights: Dictionary of keyword weights (may be None)

        Returns:
            Normalized dictionary with lowercase string keys and float values
        """
        normalized: Dict[str, float] = {}
        for key, value in (keyword_weights or {}).items():
            if not isinstance(key, str):
                continue
            try:
                normalized[key.strip().lower()] = float(value)
            except (TypeError, ValueError):
                continue
        return normalized

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize text into lowercase alphanumeric tokens.

        Args:
            text: Text to tokenize

        Returns:
            List of lowercase alphanumeric tokens
        """
        return re.findall(r"[a-z0-9]+", (text or "").lower())

    def _signal_score(
        self,
        text: str,
        target: str,
        keyword_weights: Dict[str, float],
    ) -> float:
        """Compute base signal score from text matching.

        Scoring:
        - Exact target match in text: +55.0
        - Each target token match: +8.0
        - Each keyword weight match: +weight

        Args:
            text: Text to score (link text, page content, etc.)
            target: Target description to match against
            keyword_weights: Normalized keyword weights

        Returns:
            Base signal score
        """
        haystack = f" {text.lower()} "
        target_tokens = self._tokenize(target)
        score = 0.0

        if target and target.lower() in haystack:
            score += 55.0

        for token in target_tokens:
            if f" {token} " in haystack:
                score += 8.0

        for token, weight in keyword_weights.items():
            if token and f" {token} " in haystack:
                score += weight

        return score

    def _strategy_bonus(
        self,
        url: str,
        visit_count: int,
        has_target_token: bool,
    ) -> float:
        """Compute strategy-specific bonus score.

        Q-Learning Strategy:
        - Exploration bonus: 6.0 (unvisited) decreasing to ~2.5
        - Target bonus: +18.0
        - Revisit penalty: -6.0 per revisit

        A* Strategy:
        - Goal bonus: +25.0 for target match
        - Depth penalty: -0.9 * path_depth (max -20.0)

        Args:
            url: URL to compute depth from
            visit_count: Number of times this URL has been visited
            has_target_token: Whether target appears in the text

        Returns:
            Strategy bonus score (can be negative)
        """
        if self.strategy == "q_learning":
            exploration_bonus = 6.0 if visit_count == 0 else max(0.0, 3.5 - (visit_count * 1.2))
            revisit_penalty = max(0.0, visit_count - 1) * 6.0
            target_bonus = 18.0 if has_target_token else 0.0
            return exploration_bonus + target_bonus - revisit_penalty

        # A* style: lower estimated distance to target gets higher score.
        path_depth = max(1, len([part for part in url.split("/") if part]))
        depth_penalty = min(20.0, float(path_depth) * 0.9)
        goal_bonus = 25.0 if has_target_token else 0.0
        return goal_bonus - depth_penalty

    def rank_links(
        self,
        links: List[Dict[str, str]],
        current_url: str,
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        visit_counts: Optional[Dict[str, int]] = None,
        top_k: int = 3,
    ) -> List[Dict[str, str]]:
        """Rank hyperlinks using heuristic scoring.

        Args:
            links: List of link dictionaries with href, text, title
            current_url: Current page URL (to exclude from results)
            target: Target description for scoring
            keyword_weights: Optional keyword weights for scoring
            visit_counts: Optional dictionary of visit counts per URL
            top_k: Number of top links to return

        Returns:
            List of top-k link dictionaries with initial_score added
        """
        weights = self._normalize_weights(keyword_weights)
        seen = set()
        ranked: List[Dict[str, str]] = []

        for link in links:
            url = (link.get("href") or "").strip()
            if not url or url in seen or url == current_url or "javascript:" in url.lower():
                continue
            seen.add(url)

            label = f"{link.get('text', '')} {link.get('title', '')}".strip()
            base_score = self._signal_score(label, target, weights)
            has_target_token = target.lower() in label.lower() if target else False
            visit_count = (visit_counts or {}).get(url, 0)
            strategy_score = self._strategy_bonus(url, visit_count, has_target_token)
            total = base_score + strategy_score

            ranked.append({**link, "initial_score": round(total, 2)})

        ranked.sort(key=lambda item: item.get("initial_score", 0), reverse=True)
        return ranked[:top_k]

    def score_page_content(
        self,
        page_text: str,
        page_title: str,
        url: str,
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        initial_score: float = 0.0,
        visit_count: int = 0,
    ) -> float:
        """Score page content for scout lookahead.

        Combines:
        - Text score from page content (first 12000 chars)
        - Title score with bonus for exact match
        - Strategy bonus based on URL and visit count

        Args:
            page_text: Full page text to score
            page_title: Page title
            url: Page URL
            target: Target description for scoring
            keyword_weights: Optional keyword weights
            initial_score: Starting score to add to
            visit_count: Number of visits to this page

        Returns:
            Total score rounded to 2 decimal places
        """
        weights = self._normalize_weights(keyword_weights)
        text_score = self._signal_score(page_text[:12000], target, weights)
        title_score = (
            self._signal_score(page_title, target, weights)
            + (30.0 if target.lower() in page_title.lower() else 0.0)
        )
        strategy_score = self._strategy_bonus(
            url,
            visit_count,
            target.lower() in page_title.lower() if target else False,
        )
        return round(float(initial_score) + text_score + title_score + strategy_score, 2)


__all__ = ["HeuristicScorer"]
