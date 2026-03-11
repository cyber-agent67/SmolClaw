"""Unified browser tool for SmolAgent.

Provides a single tool interface that dispatches to BrowserWrapper methods.
The agent calls browser(action="goto", url="...") to perform browser operations.
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
def browser(action: str, url: str = "", selector: str = "", text: str = "",
            fallback_instruction: str = "", field_description: str = "",
            value: str = "", target: str = "", keyword_weights: str = "",
            top_k: int = 5, tab_id: str = "", prompt: str = "",
            saas_name: str = "", schema: str = "",
            full_page: bool = False, timeout_ms: int = 5000) -> str:
    """Unified browser automation tool. Use the 'action' parameter to specify the operation.

    Actions:
    - goto: Navigate to a URL. Params: url
    - go_back: Navigate back in history.
    - click: Click an element. Params: selector, fallback_instruction (optional)
    - type_text: Type into an input. Params: selector, text
    - secure_fill: Fill a credential field securely. Params: field_description, value
    - screenshot: Capture page screenshot. Params: full_page (optional)
    - observe: Get DOM tree + page state.
    - get_page_source: Get raw HTML.
    - extract_links: Get all hyperlinks.
    - explore_astar: Rank links using A* heuristic. Params: target, keyword_weights (optional JSON), top_k
    - find_path: Depth-1 lookahead scout. Params: target, keyword_weights (optional JSON)
    - wait_for_selector: Wait for element. Params: selector, timeout_ms
    - tabs_list: List open tabs.
    - tab_create: Open new tab. Params: url (optional)
    - tab_switch: Switch to tab. Params: tab_id
    - tab_close: Close a tab. Params: tab_id
    - analyze_vision: Vision AI page analysis. Params: prompt (optional)
    - extract_settings: Extract settings from page. Params: saas_name, schema (optional JSON)
    """
    b = get_browser()

    try:
        if action == "goto":
            _run(b.goto(url))
            return json.dumps({"status": "ok", "url": url})

        elif action == "go_back":
            _run(b.go_back())
            return json.dumps({"status": "ok", "action": "go_back"})

        elif action == "click":
            fb = fallback_instruction if fallback_instruction else None
            _run(b.click(selector, fallback_instruction=fb))
            return json.dumps({"status": "ok", "selector": selector})

        elif action == "type_text":
            _run(b.type_text(selector, text))
            return json.dumps({"status": "ok", "selector": selector})

        elif action == "secure_fill":
            _run(b.secure_fill(field_description, value))
            return json.dumps({"status": "ok", "field": field_description})

        elif action == "screenshot":
            b64 = _run(b.screenshot_base64(full_page=full_page))
            return json.dumps({
                "status": "ok",
                "screenshot_base64_length": len(b64),
                "screenshot_base64": b64[:200] + "...",  # Truncated for context
            })

        elif action == "observe":
            result = _run(b.observe_page())
            return json.dumps(result, default=str)

        elif action == "get_page_source":
            source = _run(b.get_page_source())
            # Truncate to avoid blowing up context
            return json.dumps({"html_length": len(source), "html": source[:5000]})

        elif action == "extract_links":
            links = _run(b.extract_hyperlinks())
            return json.dumps({"links": links, "count": len(links)})

        elif action == "explore_astar":
            kw = json.loads(keyword_weights) if keyword_weights else None
            ranked = _run(b.explore_links_astar(target, keyword_weights=kw, top_k=top_k))
            return json.dumps({"ranked_links": ranked, "count": len(ranked)})

        elif action == "find_path":
            kw = json.loads(keyword_weights) if keyword_weights else None
            result = _run(b.find_path_to_target(target, keyword_weights=kw))
            return json.dumps(result)

        elif action == "wait_for_selector":
            _run(b.wait_for_selector(selector, timeout_ms=timeout_ms))
            return json.dumps({"status": "ok", "selector": selector})

        elif action == "tabs_list":
            tabs = _run(b.list_tabs())
            return json.dumps({"tabs": tabs})

        elif action == "tab_create":
            tab_id_new = _run(b.create_tab(url=url if url else None))
            return json.dumps({"status": "ok", "tab_id": tab_id_new})

        elif action == "tab_switch":
            _run(b.switch_tab(tab_id))
            return json.dumps({"status": "ok", "tab_id": tab_id})

        elif action == "tab_close":
            _run(b.close_tab(tab_id))
            return json.dumps({"status": "ok", "tab_id": tab_id})

        elif action == "analyze_vision":
            result = _run(b.analyze_page_vision(prompt=prompt))
            return json.dumps(result, default=str)

        elif action == "extract_settings":
            schema_dict = json.loads(schema) if schema else None
            settings = _run(b.extract_settings_vision(saas_name, schema=schema_dict))
            return json.dumps({"settings": settings, "count": len(settings)}, default=str)

        else:
            return json.dumps({"error": f"Unknown action: {action}"})

    except Exception as e:
        logger.error("Browser tool error: action=%s error=%s", action, str(e))
        return json.dumps({"error": str(e), "action": action})
