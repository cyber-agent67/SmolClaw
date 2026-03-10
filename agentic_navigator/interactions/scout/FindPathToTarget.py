"""Find path to target - the Grappling Hook interaction."""

import json
from typing import Optional

from helium import get_driver

from browser_subagents.exploration import HeuristicExplorer
from browser_subagents.services import BrowserLayerService
from agentic_navigator.entities.browser.ScoutResult import ScoutResult


class FindPathToTarget:
    @staticmethod
    def execute(target: str, keyword_values: Optional[str] = None) -> ScoutResult:
        """Uses depth-1 lookahead search to find the best link."""
        result = ScoutResult()

        driver = get_driver()
        original_window = driver.current_window_handle
        try:
            current_url = str(BrowserLayerService.current_page_state().get("url", ""))
            links_data = BrowserLayerService.extract_links()
        except Exception:
            result.error = "Failed to extract links from current page"
            return result

        weights = {}
        strategy = "q_learning"
        if keyword_values:
            try:
                payload = json.loads(keyword_values)
                if isinstance(payload, dict):
                    strategy = str(payload.get("__strategy", "q_learning"))
                    weights = {
                        key: value
                        for key, value in payload.items()
                        if key != "__strategy"
                    }
            except Exception:
                weights = {}
        visit_counts = {}
        explorer = HeuristicExplorer(strategy=strategy)
        top_candidates = explorer.rank_links(
            links=links_data,
            current_url=current_url,
            target=target,
            keyword_weights=weights,
            visit_counts=visit_counts,
            top_k=3,
        )

        best_candidate = None
        best_final_score = -1

        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])

        try:
            if not top_candidates:
                result.logs.append("No links found on current page.")

            for candidate in top_candidates:
                url = candidate["href"]
                try:
                    visit_counts[url] = visit_counts.get(url, 0) + 1
                    driver.get(url)
                    page_text = driver.find_element("tag name", "body").text[:10000]
                    final_score = explorer.score_page_content(
                        page_text=page_text,
                        page_title=driver.title,
                        url=url,
                        target=target,
                        keyword_weights=weights,
                        initial_score=float(candidate["initial_score"]),
                        visit_count=visit_counts[url],
                    )
                    relevance_score = round(final_score - float(candidate["initial_score"]), 2)
                    result.logs.append(
                        "Scouted "
                        f"{url} | TextScore: {candidate['initial_score']} | "
                        f"ContentScore: {relevance_score} | Total: {final_score} | Strategy: {explorer.strategy}"
                    )

                    if final_score > best_final_score:
                        best_final_score = final_score
                        best_candidate = candidate
                        best_candidate["final_score"] = final_score

                except Exception as e:
                    result.logs.append(f"Failed to scout {url}: {str(e)}")
        finally:
            try:
                if len(driver.window_handles) > 1:
                    driver.close()
                driver.switch_to.window(original_window)
            except Exception:
                pass

        if best_candidate and best_final_score > 0:
            result.best_url = best_candidate["href"]
            result.confidence_score = best_candidate["final_score"]
            result.reason = (
                "Grappling Hook verified content relevance using "
                f"{explorer.strategy} scoring. {best_candidate['text']}"
            )
        else:
            result.error = "No good path found."
            result.top_links_checked = [c["href"] for c in top_candidates]

        return result
