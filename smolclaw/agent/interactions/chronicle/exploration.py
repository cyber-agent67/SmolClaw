"""Chronicle exploration interaction — discovers navigation paths using A* heuristic."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExplorationStep:
    """A discovered step in a navigation path."""
    url: str
    title: str = ""
    score: float = 0.0
    depth: int = 0
    action: str = "goto"
    selector: str = ""
    instruction: str = ""


@dataclass
class ExplorationResult:
    """Result of exploring navigation paths."""
    target: str
    paths: List[List[ExplorationStep]] = field(default_factory=list)
    best_path: List[ExplorationStep] = field(default_factory=list)
    explored_urls: List[str] = field(default_factory=list)
    total_links_scored: int = 0


class ExploreNavPaths:
    """Discovers navigation paths to a target page using A* heuristic exploration.

    Uses BrowserWrapper's explore_links_astar() for link scoring and
    find_path_to_target() for depth-1 lookahead validation.
    """

    def __init__(self, browser, max_depth: int = 3, top_k: int = 5):
        self.browser = browser
        self.max_depth = max_depth
        self.top_k = top_k

    async def explore(
        self,
        target: str,
        start_url: str = "",
        keyword_weights: Optional[Dict[str, float]] = None,
    ) -> ExplorationResult:
        """Explore the current page to find paths toward a target."""
        result = ExplorationResult(target=target)

        if start_url:
            await self.browser.goto(start_url)

        try:
            current_url = await self.browser.get_current_url() or ""
            result.explored_urls.append(current_url)

            # Use A* heuristic to rank links on current page
            ranked_links = await self.browser.explore_links_astar(
                target=target,
                keyword_weights=keyword_weights,
                top_k=self.top_k,
            )
            result.total_links_scored = len(ranked_links)

            # Build paths from top-ranked links
            for link_info in ranked_links:
                step = ExplorationStep(
                    url=link_info.get("url", ""),
                    title=link_info.get("text", ""),
                    score=link_info.get("score", 0.0),
                    depth=1,
                    action="click" if link_info.get("selector") else "goto",
                    selector=link_info.get("selector", ""),
                )
                result.paths.append([step])

            # Use depth-1 lookahead for the best candidate
            if ranked_links:
                try:
                    scout_result = await self.browser.find_path_to_target(
                        target=target,
                        keyword_weights=keyword_weights,
                    )
                    if scout_result and scout_result.get("best_url"):
                        best_step = ExplorationStep(
                            url=scout_result["best_url"],
                            title=scout_result.get("title", ""),
                            score=scout_result.get("score", 0.0),
                            depth=1,
                            action="goto",
                        )
                        result.best_path = [best_step]
                except Exception as e:
                    logger.warning("Scout lookahead failed: %s", e)

            # If no best path from scout, use top A* result
            if not result.best_path and result.paths:
                result.best_path = result.paths[0]

        except Exception as e:
            logger.error("Exploration failed: %s", e)

        return result

    async def explore_deep(
        self,
        target: str,
        start_url: str = "",
        keyword_weights: Optional[Dict[str, float]] = None,
    ) -> ExplorationResult:
        """Multi-depth exploration following best links iteratively."""
        result = ExplorationResult(target=target)
        full_path: List[ExplorationStep] = []

        if start_url:
            await self.browser.goto(start_url)

        for depth in range(self.max_depth):
            current_url = await self.browser.get_current_url() or ""
            if current_url in result.explored_urls:
                break
            result.explored_urls.append(current_url)

            ranked_links = await self.browser.explore_links_astar(
                target=target,
                keyword_weights=keyword_weights,
                top_k=self.top_k,
            )
            result.total_links_scored += len(ranked_links)

            if not ranked_links:
                break

            best = ranked_links[0]
            step = ExplorationStep(
                url=best.get("url", ""),
                title=best.get("text", ""),
                score=best.get("score", 0.0),
                depth=depth + 1,
                action="click" if best.get("selector") else "goto",
                selector=best.get("selector", ""),
            )
            full_path.append(step)

            # Navigate to the best link
            if step.selector:
                try:
                    await self.browser.click(step.selector)
                except Exception:
                    await self.browser.goto(step.url)
            else:
                await self.browser.goto(step.url)

        result.best_path = full_path
        result.paths = [full_path] if full_path else []
        return result
