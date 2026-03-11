"""Heuristic explorer with Q-learning/A* style scoring for page navigation."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


class HeuristicExplorer:
    """Ranks links and pages using weighted keyword signals and strategy-specific heuristics."""

    def __init__(self, strategy: str = "q_learning"):
        selected = (strategy or "q_learning").strip().lower()
        self.strategy = selected if selected in {"q_learning", "a_star"} else "q_learning"

    @staticmethod
    def _normalize_weights(keyword_weights: Dict[str, float] | None) -> Dict[str, float]:
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
        return re.findall(r"[a-z0-9]+", (text or "").lower())

    def _signal_score(self, text: str, target: str, keyword_weights: Dict[str, float]) -> float:
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

    def _strategy_bonus(self, url: str, visit_count: int, has_target_token: bool) -> float:
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
        keyword_weights: Dict[str, float] | None = None,
        visit_counts: Dict[str, int] | None = None,
        top_k: int = 3,
    ) -> List[Dict[str, str]]:
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
        keyword_weights: Dict[str, float] | None = None,
        initial_score: float = 0.0,
        visit_count: int = 0,
    ) -> float:
        weights = self._normalize_weights(keyword_weights)
        text_score = self._signal_score(page_text[:12000], target, weights)
        title_score = self._signal_score(page_title, target, weights) + (30.0 if target.lower() in page_title.lower() else 0.0)
        strategy_score = self._strategy_bonus(url, visit_count, target.lower() in page_title.lower() if target else False)
        return round(float(initial_score) + text_score + title_score + strategy_score, 2)