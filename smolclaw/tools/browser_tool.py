"""Browser automation tool for SmolClaw agent.

Provides browser navigation and interaction capabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from smolagents import tool

logger = logging.getLogger(__name__)

# Module-level browser instance (set by the runner)
_browser = None


def set_browser(browser_instance) -> None:
    """Set the shared browser instance for all tool calls."""
    global _browser
    _browser = browser_instance


def get_browser():
    """Get the shared browser instance."""
    if _browser is None:
        raise RuntimeError("Browser not initialized. Call set_browser() first.")
    return _browser


def _run(coro):
    """Run an async coroutine from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@tool
def browser(
    action: str,
    url: str = "",
    selector: str = "",
    text: str = "",
    fallback_instruction: str = "",
    field_description: str = "",
    value: str = "",
    target: str = "",
    keyword_weights: str = "",
    top_k: int = 5,
    tab_id: str = "",
    prompt: str = "",
    saas_name: str = "",
    schema: str = "",
    full_page: bool = False,
    timeout_ms: int = 5000,
) -> str:
    """Unified browser automation tool.
    
    Args:
        action: The action to perform (goto, click, type, etc.)
        url: URL to navigate to
        selector: CSS selector for element interaction
        text: Text to type or search for
        fallback_instruction: Optional instruction for fallback behavior
        field_description: Description of field for secure fill
        value: Value to set
        target: Target description for exploration
        keyword_weights: JSON string of keyword weights
        top_k: Number of top results to return
        tab_id: Tab ID for tab operations
        prompt: Prompt for vision analysis
        saas_name: SaaS name for settings extraction
        schema: Schema for settings extraction
        full_page: Whether to capture full page screenshot
        timeout_ms: Timeout in milliseconds
    
    Actions:
    - goto: Navigate to a URL. Params: url
    - go_back: Navigate back in history.
    - click: Click an element. Params: selector, fallback_instruction (optional)
    - type_text: Type text into an input. Params: selector, text
    - secure_fill: Securely fill credential field. Params: field_description, value
    - wait_for_selector: Wait for element. Params: selector, timeout_ms
    - observe_page: Get page observation. Params: none
    - extract_hyperlinks: Get all links. Params: none
    - explore_links_astar: A* link exploration. Params: target, keyword_weights, top_k
    - find_path_to_target: Scout navigation. Params: target, keyword_weights
    - analyze_page_vision: Vision analysis. Params: prompt
    - extract_settings_vision: Extract settings. Params: saas_name, schema
    - list_tabs: List open tabs. Params: none
    - create_tab: Create new tab. Params: url (optional)
    - switch_tab: Switch to tab. Params: tab_id
    - close_tab: Close tab. Params: tab_id
    """
    browser = get_browser()
    
    try:
        if action == "goto":
            return _run(browser.goto(url))
        
        elif action == "go_back":
            return _run(browser.go_back())
        
        elif action == "click":
            return _run(
                browser.click(selector, fallback_instruction=fallback_instruction)
            )
        
        elif action == "type_text":
            return _run(browser.type_text(selector, text))
        
        elif action == "secure_fill":
            return _run(browser.secure_fill(field_description, value))
        
        elif action == "wait_for_selector":
            return _run(browser.wait_for_selector(selector, timeout_ms))
        
        elif action == "observe_page":
            return json.dumps(_run(browser.observe_page()), indent=2)
        
        elif action == "extract_hyperlinks":
            links = _run(browser.extract_hyperlinks())
            return json.dumps({"links": links, "count": len(links)}, indent=2)
        
        elif action == "explore_links_astar":
            weights = json.loads(keyword_weights) if keyword_weights else None
            ranked = _run(
                browser.explore_links_astar(target, keyword_weights=weights, top_k=top_k)
            )
            return json.dumps({"ranked_links": ranked}, indent=2)
        
        elif action == "find_path_to_target":
            weights = json.loads(keyword_weights) if keyword_weights else None
            result = _run(browser.find_path_to_target(target, keyword_weights=weights))
            return json.dumps(result, indent=2)
        
        elif action == "analyze_page_vision":
            result = _run(browser.analyze_page_vision(prompt=prompt))
            return json.dumps(result, indent=2)
        
        elif action == "extract_settings_vision":
            schema_dict = json.loads(schema) if schema else None
            result = _run(
                browser.extract_settings_vision(saas_name, schema=schema_dict)
            )
            return json.dumps(result, indent=2)
        
        elif action == "list_tabs":
            tabs = _run(browser.list_tabs())
            return json.dumps({"tabs": tabs}, indent=2)
        
        elif action == "create_tab":
            new_tab_id = _run(browser.create_tab(url if url else None))
            return json.dumps({"tab_id": new_tab_id, "url": url}, indent=2)
        
        elif action == "switch_tab":
            _run(browser.switch_tab(tab_id))
            return json.dumps({"switched_to": tab_id}, indent=2)
        
        elif action == "close_tab":
            _run(browser.close_tab(tab_id))
            return json.dumps({"closed": tab_id}, indent=2)
        
        else:
            return f"Unknown action: {action}"
    
    except Exception as e:
        logger.error(f"Browser action '{action}' failed: {e}")
        return f"Error: {e}"


__all__ = ["browser", "set_browser", "get_browser"]
