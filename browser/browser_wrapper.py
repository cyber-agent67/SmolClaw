"""Unified browser wrapper — custom Stagehand equivalent.

Provides a single interface for all browser operations: navigation, interaction,
observation, A* exploration, tab management, and vision analysis.
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from .config import BrowserConfig

logger = logging.getLogger(__name__)


@dataclass
class TabInfo:
    """Tracked browser tab."""
    id: str
    url: str = ""
    active: bool = False
    window_handle: str = ""
    history: list[str] = field(default_factory=list)


class BrowserWrapper:
    """Unified browser interface — custom Stagehand equivalent.

    Wraps Selenium/Helium for browser automation and integrates:
    - Core navigation (goto, back, click, type)
    - Secure credential filling
    - DOM observation and page state capture
    - A* hyperlink exploration (Layer 3)
    - Depth-1 lookahead scouting
    - Tab management
    - Vision analysis (delegated to VisionClient)
    """

    def __init__(self, config: BrowserConfig | None = None):
        self.config = config or BrowserConfig()
        self._driver: Any = None
        self._tabs: dict[str, TabInfo] = {}
        self._current_tab_id: str | None = None
        self._navigation_stack: list[str] = []
        self._q_values: dict[str, float] = {}
        self._visit_counts: dict[str, int] = {}
        self._vision_client: Any = None

    @property
    def driver(self) -> Any:
        """Get the Selenium WebDriver instance."""
        if self._driver is None:
            raise RuntimeError("Browser not launched. Call launch() first.")
        return self._driver

    # --- Session lifecycle ---

    async def launch(self) -> None:
        """Launch browser with configured options."""
        try:
            import helium
            from selenium.webdriver import Chrome, ChromeOptions
        except ImportError as e:
            raise RuntimeError(f"Browser dependencies not installed: {e}")

        options = ChromeOptions()
        if self.config.headless:
            options.add_argument("--headless=new")

        if self.config.bot_evasion:
            for arg in self.config.BOT_EVASION_ARGS:
                options.add_argument(arg)

        options.add_argument(f"--window-size={self.config.window_width},{self.config.window_height}")

        if self.config.cdp_url:
            options.debugger_address = self.config.cdp_url
            self._driver = Chrome(options=options)
        else:
            self._driver = Chrome(options=options)

        helium.set_driver(self._driver)

        # Register initial tab
        handle = self._driver.current_window_handle
        tab = TabInfo(id="tab_0", url=self._driver.current_url, active=True, window_handle=handle)
        self._tabs["tab_0"] = tab
        self._current_tab_id = "tab_0"
        logger.info("Browser launched", extra={"headless": self.config.headless})

    async def close(self) -> None:
        """Close the browser and clean up."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
            self._tabs.clear()
            self._current_tab_id = None
            self._navigation_stack.clear()
            logger.info("Browser closed")

    # --- Core navigation ---

    async def goto(self, url: str) -> None:
        """Navigate to a URL."""
        self.driver.get(url)
        self._navigation_stack.append(url)
        if self._current_tab_id and self._current_tab_id in self._tabs:
            tab = self._tabs[self._current_tab_id]
            tab.url = url
            tab.history.append(url)
        logger.info("Navigated to %s", url)

    async def go_back(self) -> None:
        """Navigate back in browser history."""
        if len(self._navigation_stack) > 1:
            self._navigation_stack.pop()
            self.driver.back()
        else:
            self.driver.back()

    async def get_current_url(self) -> str:
        """Get the current page URL."""
        return self.driver.current_url

    async def get_page_title(self) -> str:
        """Get the current page title."""
        return self.driver.title

    # --- Interaction ---

    async def click(self, selector: str, fallback_instruction: str | None = None) -> None:
        """Click an element by CSS selector with optional AI fallback."""
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import (
            NoSuchElementException,
            ElementNotInteractableException,
        )

        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.click()
        except (NoSuchElementException, ElementNotInteractableException):
            if fallback_instruction:
                # Try XPath text matching as fallback
                try:
                    xpath = f"//*[contains(text(), '{fallback_instruction}')]"
                    element = self.driver.find_element(By.XPATH, xpath)
                    element.click()
                except Exception:
                    raise RuntimeError(
                        f"Click failed: selector '{selector}' not found, "
                        f"fallback '{fallback_instruction}' also failed"
                    )
            else:
                raise

    async def type_text(self, selector: str, text: str) -> None:
        """Type text into an input field."""
        from selenium.webdriver.common.by import By

        element = self.driver.find_element(By.CSS_SELECTOR, selector)
        element.clear()
        element.send_keys(text)

    async def secure_fill(self, field_description: str, value: str) -> None:
        """Securely fill a credential field without exposing value to LLM context.

        Uses field_description to locate the field, then fills it directly.
        The value is never logged or sent to the LLM.
        """
        from selenium.webdriver.common.by import By

        # Try common password/credential selectors
        selectors = [
            'input[type="password"]',
            f'input[placeholder*="{field_description}" i]',
            f'input[aria-label*="{field_description}" i]',
            f'input[name*="{field_description}" i]',
        ]

        for sel in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, sel)
                element.clear()
                element.send_keys(value)
                return
            except Exception:
                continue

        raise RuntimeError(f"Could not find field matching '{field_description}'")

    async def wait_for_selector(self, selector: str, timeout_ms: int = 5000) -> None:
        """Wait for an element to appear on the page."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        timeout_s = timeout_ms / 1000
        WebDriverWait(self.driver, timeout_s).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    # --- Observation ---

    async def screenshot(self, full_page: bool = False) -> bytes:
        """Capture a screenshot of the current page."""
        png_bytes = self.driver.get_screenshot_as_png()
        return png_bytes

    async def screenshot_base64(self, full_page: bool = False) -> str:
        """Capture a screenshot as base64-encoded string."""
        png_bytes = await self.screenshot(full_page=full_page)
        return base64.b64encode(png_bytes).decode("ascii")

    async def observe_page(self) -> dict:
        """Get DOM tree + page state as structured data.

        Delegates to BrowserLayerService for consistent implementation.
        """
        from smolclaw.tools.smolhand.services import BrowserLayerService

        try:
            snapshot_json = BrowserLayerService.page_snapshot_json()
            return json.loads(snapshot_json)
        except Exception as e:
            logger.warning("Layer service observe failed: %s, using fallback", e)
            # Fallback to direct implementation
            url = self.driver.current_url
            title = self.driver.title
            page_source = self.driver.page_source

            interactive = self.driver.execute_script("""
                var elements = [];
                var interactives = document.querySelectorAll(
                    'a, button, input, select, textarea, [role="button"], [role="link"], [onclick]'
                );
                for (var i = 0; i < Math.min(interactives.length, 200); i++) {
                    var el = interactives[i];
                    var rect = el.getBoundingClientRect();
                    elements.push({
                        tag: el.tagName.toLowerCase(),
                        type: el.type || '',
                        text: (el.innerText || el.value || '').substring(0, 100),
                        href: el.href || '',
                        name: el.name || '',
                        id: el.id || '',
                        aria_label: el.getAttribute('aria-label') || '',
                        placeholder: el.placeholder || '',
                        visible: rect.width > 0 && rect.height > 0,
                        x: rect.x, y: rect.y, width: rect.width, height: rect.height
                    });
                }
                return elements;
            """)

            headings = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('h1,h2,h3')).map(
                    h => h.innerText.trim()
                ).filter(t => t.length > 0).slice(0, 20);
            """)

            return {
                "url": url,
                "title": title,
                "headings": headings,
                "interactive_elements": interactive,
                "page_source_length": len(page_source),
            }

    async def get_page_source(self) -> str:
        """Get raw HTML source of the current page."""
        return self.driver.page_source

    async def extract_hyperlinks(self) -> list[dict]:
        """Get all hyperlinks on the current page.

        Delegates to BrowserLayerService for consistent implementation.
        """
        from smolclaw.tools.smolhand.services import BrowserLayerService

        try:
            return BrowserLayerService.extract_links()
        except Exception as e:
            logger.warning("Layer service extract_links failed: %s, using fallback", e)
            # Fallback to direct implementation
            links = self.driver.execute_script("""
                var links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(function(link) {
                    return {
                        href: link.href,
                        text: link.innerText.trim(),
                        title: link.title || ''
                    };
                });
            """)
            return links or []

    # --- A* Navigation (Layer 3) ---

    async def explore_links_astar(
        self,
        target: str,
        keyword_weights: dict[str, float] | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Rank page hyperlinks using A* heuristic to find best path to target.

        Delegates to DOMExplorerLayerService for consistent implementation.
        """
        from smolclaw.tools.smolhand.services import DOMExplorerLayerService

        try:
            result = DOMExplorerLayerService.explore(
                target=target,
                keyword_weights=keyword_weights,
                top_k=top_k,
            )
            return result.get("ranked_links", [])
        except Exception as e:
            logger.warning("Layer service explore failed: %s, using fallback", e)
            # Fallback to existing implementation
            try:
                from smolclaw.tools.smolhand.scoring.heuristic_scorer import HeuristicScorer
            except ImportError:
                # Fallback: basic keyword matching
                links = await self.extract_hyperlinks()
                target_lower = target.lower()
                scored = []
                for link in links:
                    text = (link.get("text", "") + " " + link.get("title", "")).lower()
                    score = 55.0 if target_lower in text else 0.0
                    for token in target_lower.split():
                        if token in text:
                            score += 8.0
                    scored.append({**link, "score": score})
                scored.sort(key=lambda x: x["score"], reverse=True)
                return scored[:top_k]

            explorer = HeuristicScorer(strategy="a_star")
            links = await self.extract_hyperlinks()
            current_url = await self.get_current_url()

            ranked = explorer.rank_links(
                links=links,
                current_url=current_url,
                target=target,
                keyword_weights=keyword_weights,
                visit_counts=self._visit_counts,
                top_k=top_k,
            )
            return ranked

    async def find_path_to_target(
        self,
        target: str,
        keyword_weights: dict[str, float] | None = None,
    ) -> dict:
        """Depth-1 lookahead scout — opens top links, scores content, returns best URL.

        Delegates to scout interaction for consistent implementation.
        """
        from smolclaw.agent.interactions.scout.FindPathToTarget import FindPathToTarget

        try:
            # Use the scout interaction which has the full lookahead implementation
            keyword_values = json.dumps(keyword_weights) if keyword_weights else None
            result = FindPathToTarget.execute(target, keyword_values)

            if result.error:
                return {
                    "error": result.error,
                    "logs": result.logs,
                    "top_links_checked": result.top_links_checked,
                }

            return {
                "best_url": result.best_url,
                "confidence": result.confidence_score,
                "reason": result.reason,
                "logs": result.logs,
            }
        except Exception as e:
            logger.warning("Scout interaction failed: %s, using fallback", e)
            # Fallback to existing implementation
            return await self._find_path_to_target_fallback(target, keyword_weights)

    async def _find_path_to_target_fallback(
        self,
        target: str,
        keyword_weights: dict[str, float] | None = None,
    ) -> dict:
        """Fallback implementation for find_path_to_target."""
        try:
            from smolclaw.tools.smolhand.scoring.heuristic_scorer import HeuristicScorer
        except ImportError:
            ranked = await self.explore_links_astar(target, keyword_weights, top_k=1)
            if ranked:
                return {
                    "best_url": ranked[0].get("href", ""),
                    "confidence": ranked[0].get("score", 0.0) / 100.0,
                    "reason": f"Best A* match: {ranked[0].get('text', '')}",
                }
            return {"best_url": None, "confidence": 0.0, "reason": "No links found"}

        explorer = HeuristicScorer(strategy="a_star")
        links = await self.extract_hyperlinks()
        current_url = await self.get_current_url()

        ranked = explorer.rank_links(
            links=links,
            current_url=current_url,
            target=target,
            keyword_weights=keyword_weights,
            visit_counts=self._visit_counts,
            top_k=3,
        )

        if not ranked:
            return {"best_url": None, "confidence": 0.0, "reason": "No links found"}

        best_url = None
        best_score = -1.0
        best_reason = ""
        original_handle = self.driver.current_window_handle

        for candidate in ranked[:3]:
            href = candidate.get("href", "")
            if not href:
                continue
            try:
                self.driver.execute_script(f"window.open('{href}', '_blank');")
                handles = self.driver.window_handles
                self.driver.switch_to.window(handles[-1])

                page_text = self.driver.execute_script(
                    "return document.title + ' ' + document.body.innerText.substring(0, 20000);"
                )
                score = explorer.score_page_content(
                    page_text=page_text,
                    page_title=self.driver.title,
                    url=href,
                    target=target,
                    keyword_weights=keyword_weights,
                )

                if score > best_score:
                    best_score = score
                    best_url = href
                    best_reason = f"Content score {score:.2f} for '{self.driver.title}'"

                self.driver.close()
                self.driver.switch_to.window(original_handle)
            except Exception as e:
                logger.warning("Scout failed for %s: %s", href, e)
                try:
                    self.driver.switch_to.window(original_handle)
                except Exception:
                    pass

        return {
            "best_url": best_url,
            "confidence": min(best_score / 100.0, 1.0) if best_score > 0 else 0.0,
            "reason": best_reason,
        }

    # --- Tab management ---

    async def list_tabs(self) -> list[dict]:
        """List all open browser tabs."""
        result = []
        for tab_id, tab in self._tabs.items():
            result.append({
                "id": tab_id,
                "url": tab.url,
                "active": tab.id == self._current_tab_id,
            })
        return result

    async def create_tab(self, url: str | None = None) -> str:
        """Open a new browser tab, optionally navigating to a URL."""
        self.driver.execute_script("window.open('about:blank', '_blank');")
        handles = self.driver.window_handles
        new_handle = handles[-1]
        self.driver.switch_to.window(new_handle)

        tab_id = f"tab_{len(self._tabs)}"
        tab = TabInfo(id=tab_id, url="about:blank", active=True, window_handle=new_handle)

        # Deactivate previous tab
        if self._current_tab_id and self._current_tab_id in self._tabs:
            self._tabs[self._current_tab_id].active = False

        self._tabs[tab_id] = tab
        self._current_tab_id = tab_id

        if url:
            self.driver.get(url)
            tab.url = url

        return tab_id

    async def switch_tab(self, tab_id: str) -> None:
        """Switch to a specific browser tab by its ID."""
        if tab_id not in self._tabs:
            raise ValueError(f"Tab '{tab_id}' not found")

        tab = self._tabs[tab_id]
        self.driver.switch_to.window(tab.window_handle)

        # Update active states
        if self._current_tab_id and self._current_tab_id in self._tabs:
            self._tabs[self._current_tab_id].active = False
        tab.active = True
        self._current_tab_id = tab_id
        tab.url = self.driver.current_url

    async def close_tab(self, tab_id: str) -> None:
        """Close a browser tab by its ID."""
        if tab_id not in self._tabs:
            raise ValueError(f"Tab '{tab_id}' not found")

        tab = self._tabs[tab_id]
        self.driver.switch_to.window(tab.window_handle)
        self.driver.close()
        del self._tabs[tab_id]

        # Switch to another tab if available
        if self._tabs:
            fallback_id = next(iter(self._tabs))
            fallback = self._tabs[fallback_id]
            self.driver.switch_to.window(fallback.window_handle)
            fallback.active = True
            self._current_tab_id = fallback_id
        else:
            self._current_tab_id = None

    # --- Vision (delegated) ---

    async def analyze_page_vision(self, prompt: str = "") -> dict:
        """Use vision AI to analyze the current page via SmolEyes."""
        from smolclaw.tools.smoleyes.runtime import describe_page_visual

        try:
            return describe_page_visual(prompt_hint=prompt)
        except Exception as e:
            logger.warning("Florence vision failed: %s, using fallback", e)
            # Fallback to custom vision client if configured
            screenshot_b64 = await self.screenshot_base64()
            if self._vision_client is None:
                return {
                    "error": "Vision client not configured",
                    "screenshot_captured": True,
                    "screenshot_base64_length": len(screenshot_b64),
                }

            result = await self._vision_client.complete_with_image_async(
                prompt=prompt or "Describe what you see on this page.",
                image_bytes=base64.b64decode(screenshot_b64),
            )
            return {"analysis": result, "url": await self.get_current_url()}

    async def extract_settings_vision(
        self,
        saas_name: str,
        schema: dict | None = None,
    ) -> list[dict]:
        """Extract settings from current page using vision AI."""
        screenshot_b64 = await self.screenshot_base64()
        if self._vision_client is None:
            return [{"error": "Vision client not configured"}]

        result = await self._vision_client.extract_settings(
            screenshot_base64=screenshot_b64,
            page_url=await self.get_current_url(),
            saas_name=saas_name,
            schema=schema,
        )
        return result

    def set_vision_client(self, client: Any) -> None:
        """Set the vision client for page analysis and settings extraction."""
        self._vision_client = client
