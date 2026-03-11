"""DOM exploration operations for AI Agent A* link ranking.

This module provides A* heuristic exploration logic used by the AI Agent
to find the most relevant links on a page.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from smolclaw.smolhand.layers.layer1_browser.page_operations import ExtractHyperlinks, ReadCurrentPage
from smolclaw.smolhand.scoring.heuristic_scorer import HeuristicScorer
from smolclaw.agent.tools.exploration.entities import ExplorationResultEntity, RankedLinkEntity


class ExploreCurrentPageAStar:
    """Explores current page hyperlinks using A* heuristic scoring."""

    @staticmethod
    def execute(
        target: str,
        keyword_weights: Optional[Dict[str, float]] = None,
        top_k: int = 5,
    ) -> ExplorationResultEntity:
        """
        Execute A* exploration of current page links.

        Args:
            target: Target description for link ranking
            keyword_weights: Optional keyword weights for scoring
            top_k: Number of top links to return

        Returns:
            ExplorationResultEntity with ranked links
        """
        page = ReadCurrentPage.execute()
        links = ExtractHyperlinks.execute()

        explorer = HeuristicScorer(strategy="a_star")
        ranked = explorer.rank_links(
            links=[{"href": l.href, "text": l.text, "title": l.title} for l in links],
            current_url=page.url,
            target=target,
            keyword_weights=keyword_weights or {},
            visit_counts={},
            top_k=top_k,
        )

        ranked_entities = [
            RankedLinkEntity(
                href=item.get("href", ""),
                text=item.get("text", ""),
                title=item.get("title", ""),
                initial_score=float(item.get("initial_score", 0.0)),
            )
            for item in ranked
        ]

        return ExplorationResultEntity(
            target=target,
            strategy="a_star",
            current_url=page.url,
            title=page.title,
            ranked_links=ranked_entities,
        )


__all__ = ["ExploreCurrentPageAStar"]
