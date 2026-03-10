"""Find path to target - the Grappling Hook interaction."""

import json
from typing import Optional

from helium import get_driver

from agentic_navigator.entities.browser.ScoutResult import ScoutResult


class FindPathToTarget:
    @staticmethod
    def execute(target: str, keyword_values: Optional[str] = None) -> ScoutResult:
        """Uses depth-1 lookahead search to find the best link."""
        result = ScoutResult()

        driver = get_driver()
        original_window = driver.current_window_handle
        current_url = driver.current_url

        try:
            links_data = driver.execute_script(
                """
                var links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(function(link) {
                    return {
                        href: link.href,
                        text: link.innerText.trim(),
                        title: link.title || ''
                    };
                });
                """
            )
        except Exception:
            result.error = "Failed to extract links from current page"
            return result

        weights = {}
        if keyword_values:
            try:
                weights = json.loads(keyword_values)
            except Exception:
                weights = {}

        def get_score(text: str, target_text: str, weight_map: dict) -> int:
            candidate = text.lower()
            desired = target_text.lower()
            score = 0
            if desired in candidate:
                score += 50
            for token, value in weight_map.items():
                if token.lower() in candidate:
                    score += value
            return score

        scored_candidates = []
        seen_hrefs = set()

        for link in links_data:
            href = link["href"]
            if href in seen_hrefs or href == current_url or "javascript:" in href:
                continue
            seen_hrefs.add(href)

            score = get_score(link["text"] + " " + link["title"], target, weights)
            scored_candidates.append({**link, "initial_score": score})

        scored_candidates.sort(key=lambda x: x["initial_score"], reverse=True)
        top_candidates = scored_candidates[:3]

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
                    driver.get(url)
                    page_text = driver.find_element("tag name", "body").text[:10000]

                    relevance_score = get_score(page_text, target, weights)
                    if target.lower() in driver.title.lower():
                        relevance_score += 30

                    final_score = candidate["initial_score"] + relevance_score
                    result.logs.append(
                        "Scouted "
                        f"{url} | TextScore: {candidate['initial_score']} | "
                        f"ContentScore: {relevance_score} | Total: {final_score}"
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
            result.reason = f"Grappling Hook verified content relevance. {best_candidate['text']}"
        else:
            result.error = "No good path found."
            result.top_links_checked = [c["href"] for c in top_candidates]

        return result
