"""Interactions for Layer 3 (A* DOM exploration)."""

from __future__ import annotations

from typing import Dict

from browser_subagents.exploration import HeuristicExplorer
from browser_subagents.layers.layer1_browser.interactions import ExtractHyperlinks, ReadCurrentPage
from browser_subagents.layers.layer3_dom_explorer.entities import ExplorationResultEntity, RankedLinkEntity


class ExploreCurrentPageAStar:
    @staticmethod
    def execute(target: str, keyword_weights: Dict[str, float] | None = None, top_k: int = 5) -> ExplorationResultEntity:
        page = ReadCurrentPage.execute()
        links = ExtractHyperlinks.execute()

        explorer = HeuristicExplorer(strategy="a_star")
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
