"""Tool registry that bridges EIM interactions to smolagents @tool wrappers.

This module registers all tools available to the AI Agent:
- Browser Tools: Navigation, tabs, DOM access
- Vision Tool: Florence-2 visual analysis
- Exploration Tool: A* heuristic link ranking
- Q-Learning Tool: Navigation scoring and learning
- Scout Tool: Depth-1 lookahead path finding
"""

import json
from typing import Optional, Tuple

from helium import get_driver
from smolagents import WebSearchTool, tool

from smolclaw.tools.smolhand.services import BrowserLayerService
from smolclaw.agent.entities.browser.Browser import Browser
from smolclaw.agent.entities.browser.NavigationStack import NavigationStack
from smolclaw.agent.entities.browser.Tab import Tab

_navigation_stack = NavigationStack()
_tabs = {}
_tab_counter = 0
_current_tab_id = None


def _registry_tools():
    """Single source of truth for tool registration order."""
    return [
        WebSearchTool(),
        go_back,
        close_popups,
        search_item_ctrl_f,
        get_DOM_Tree,
        get_browser_snapshot,
        # SmolEyes vision tools
        analyze_visual_context,
        describe_page_visual,
        find_visual_element,
        extract_text_from_screenshot,
        detect_page_objects,
        # Other intelligence tools
        explore_dom_with_astar,
        score_task_progress_q_learning,
        # Browser tools
        list_open_tabs,
        set_browser_url,
        create_new_tab,
        switch_to_tab,
        close_tab,
        find_path_to_target,
        get_address,
        get_geolocation,
        think,
        quit_browser,
    ]


def _tool_name(tool_obj) -> str:
    """Normalizes function/class tool objects to a displayable name."""
    if hasattr(tool_obj, "name") and tool_obj.name:
        return str(tool_obj.name)
    if hasattr(tool_obj, "__name__"):
        return str(tool_obj.__name__)
    return tool_obj.__class__.__name__


def _set_active_tab(tab_id: Optional[str]) -> None:
    for candidate_id, tab in _tabs.items():
        tab.active = candidate_id == tab_id


def _sync_tab_snapshot(tab_id: str, append_history: bool = False) -> None:
    tab = _tabs.get(tab_id)
    if tab is None:
        return

    try:
        driver = get_driver()
        tab.window_handle = driver.current_window_handle
        current_url = driver.current_url
        tab.url = current_url
        if append_history and current_url and (not tab.history or tab.history[-1] != current_url):
            tab.history.append(current_url)
    except Exception:
        return


def _probe_current_page() -> Tuple[bool, str]:
    try:
        page = BrowserLayerService.current_page_state()
        current_url = str(page.get("url", ""))
        page_source = page.get("page_source", "")
        if not page_source:
            return False, "Current page source is empty."
        return True, current_url
    except Exception as exc:
        return False, str(exc)


def _activate_live_tab(exclude_tab_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    from smolclaw.agent.interactions.tab.Switch import SwitchTab

    original_tab_id = _current_tab_id
    candidate_ids = [tab_id for tab_id in _tabs.keys() if tab_id != exclude_tab_id]
    for tab_id in candidate_ids:
        if not SwitchTab.execute(_tabs, tab_id):
            continue

        is_live, detail = _probe_current_page()
        if is_live:
            _sync_tab_snapshot(tab_id)
            _set_active_tab(tab_id)
            return tab_id, detail

    if original_tab_id and original_tab_id in _tabs:
        SwitchTab.execute(_tabs, original_tab_id)
        _sync_tab_snapshot(original_tab_id)
        _set_active_tab(original_tab_id)

    return None, None


def _recover_live_page(action_name: str) -> Optional[str]:
    global _current_tab_id

    if _current_tab_id and _current_tab_id in _tabs:
        _set_active_tab(_current_tab_id)
        _sync_tab_snapshot(_current_tab_id)
        is_live, _ = _probe_current_page()
        if is_live:
            return None

    recovered_tab_id, recovered_url = _activate_live_tab(exclude_tab_id=_current_tab_id)
    if recovered_tab_id:
        _current_tab_id = recovered_tab_id
        return (
            f"Current page was unavailable. Switched to {recovered_tab_id} "
            f"({recovered_url}) before running {action_name}."
        )

    return None


def get_navigation_stack() -> NavigationStack:
    """Exposes the shared navigation stack for orchestrators/tests."""
    return _navigation_stack


@tool
def get_DOM_Tree() -> str:
    """Retrieves the full DOM tree of the current page as a JSON string."""
    recovery_note = _recover_live_page("get_DOM_Tree")
    dom_tree_json = BrowserLayerService.dom_tree_json()
    if recovery_note:
        return f"{recovery_note}\n{dom_tree_json}"
    return dom_tree_json


@tool
def get_browser_snapshot() -> str:
    """Returns a normalized JSON snapshot of URL/title/DOM/link context from the shared browser tool layer."""
    recovery_note = _recover_live_page("get_browser_snapshot")
    payload = BrowserLayerService.page_snapshot_json()
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def analyze_visual_context(prompt_hint: str = "") -> str:
    """Use SmolEyes vision AI to analyze the current page's visual content.
    
    This tool captures a screenshot and uses Florence-2 to generate
    a detailed visual description guided by the prompt.
    
    Args:
        prompt_hint: Optional hint to guide the visual analysis
    
    Returns:
        JSON string with visual analysis results
    """
    from smolclaw.tools.smoleyes.tools import analyze_visual_context as eyes_tool

    recovery_note = _recover_live_page("analyze_visual_context")
    payload = eyes_tool(prompt_hint)
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def describe_page_visual(prompt_hint: str = "") -> str:
    """Describe current page using SmolEyes vision analysis.
    
    Similar to analyze_visual_context but focused on detailed visual description.
    
    Args:
        prompt_hint: Optional hint to guide analysis
    
    Returns:
        JSON string with detailed visual description
    """
    from smolclaw.tools.smoleyes.tools import describe_page_visual_tool as eyes_tool

    recovery_note = _recover_live_page("describe_page_visual")
    payload = eyes_tool(prompt_hint)
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def find_visual_element(description: str, confidence_threshold: float = 0.5) -> str:
    """Find visual element on page by natural language description using SmolEyes.
    
    Uses Florence-2 object detection to find elements like:
    - "blue submit button"
    - "search icon"
    - "navigation menu"
    
    Args:
        description: Natural language description of element
        confidence_threshold: Minimum confidence (0.0-1.0)
    
    Returns:
        JSON string with found elements
    """
    from smolclaw.tools.smoleyes.tools import find_visual_element_tool as eyes_tool

    recovery_note = _recover_live_page("find_visual_element")
    payload = eyes_tool(description, confidence_threshold)
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def extract_text_from_screenshot() -> str:
    """Extract all text visible on current page using SmolEyes OCR.
    
    Uses Florence-2 OCR to extract text from images, buttons, and custom fonts.
    
    Returns:
        JSON string with extracted text
    """
    from smolclaw.tools.smoleyes.tools import extract_text_from_screenshot as eyes_tool

    recovery_note = _recover_live_page("extract_text_from_screenshot")
    payload = eyes_tool()
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def detect_page_objects() -> str:
    """Detect all objects on current page using SmolEyes.
    
    Uses Florence-2 to detect buttons, images, text blocks, forms, etc.
    
    Returns:
        JSON string with detected objects
    """
    from smolclaw.tools.smoleyes.tools import detect_page_objects as eyes_tool

    recovery_note = _recover_live_page("detect_page_objects")
    payload = eyes_tool()
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def explore_dom_with_astar(target: str, keyword_values: str = None, top_k: int = 5) -> str:
    """Use A* heuristics to rank hyperlinks on the current page by relevance.
    
    Args:
        target: Target description for link ranking
        keyword_values: Optional JSON string with keyword weights
        top_k: Number of top links to return
    """
    from smolclaw.agent.tools.exploration import explore_dom_with_astar as explore_tool

    recovery_note = _recover_live_page("explore_dom_with_astar")
    payload = explore_tool(target, keyword_values=keyword_values, top_k=top_k)
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def score_task_progress_q_learning(task_prompt: str, llm_score: float = None, action_name: str = "observe") -> str:
    """AI Agent tool: computes task/page vector reward and updates Q-value for navigation learning.
    
    Args:
        task_prompt: Natural language task description
        llm_score: Optional LLM-provided score (0.0-1.0)
        action_name: Name of action that led to current state
    """
    from smolclaw.agent.tools.q_learning import score_task_progress_q_learning as q_tool

    recovery_note = _recover_live_page("score_task_progress_q_learning")
    payload = q_tool(task_prompt, llm_score=llm_score, action_name=action_name)
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def set_browser_url(url: str) -> str:
    """Navigate the browser to a specific URL.
    
    Args:
        url: URL to navigate to
    """
    from smolclaw.agent.interactions.navigation.GoToURL import GoToURL

    global _current_tab_id

    current_tab = _tabs.get(_current_tab_id) if _current_tab_id else None
    result = GoToURL.execute(url, _navigation_stack, current_tab)
    if _current_tab_id:
        _sync_tab_snapshot(_current_tab_id, append_history=True)
    return result


@tool
def create_new_tab(url: str = None) -> str:
    """Create a new browser tab and optionally navigate to a URL.
    
    Args:
        url: Optional URL to navigate to after creating tab
    """
    from smolclaw.agent.interactions.tab.Create import CreateTab

    global _tab_counter, _current_tab_id

    _, _tab_counter, tab_id = CreateTab.execute(_tabs, _tab_counter, url)
    _current_tab_id = tab_id
    _set_active_tab(tab_id)
    _sync_tab_snapshot(tab_id, append_history=True)
    return f"Created new tab with ID: {tab_id}"


@tool
def switch_to_tab(tab_id: str) -> str:
    """Switch to the specified browser tab.
    
    Args:
        tab_id: ID of tab to switch to
    """
    from smolclaw.agent.interactions.tab.Switch import SwitchTab

    global _current_tab_id

    success = SwitchTab.execute(_tabs, tab_id)
    if success:
        _current_tab_id = tab_id
        _set_active_tab(tab_id)
        _sync_tab_snapshot(tab_id)
        return f"Switched to tab: {tab_id}"
    return f"Failed to switch to tab: {tab_id}"


@tool
def close_tab(tab_id: str) -> str:
    """Close the specified browser tab.
    
    Args:
        tab_id: ID of tab to close
    """
    from smolclaw.agent.interactions.tab.Close import CloseTab

    global _current_tab_id

    success, new_current = CloseTab.execute(_tabs, tab_id, _current_tab_id)
    _current_tab_id = new_current
    _set_active_tab(_current_tab_id)
    if success:
        return f"Closed tab: {tab_id}"
    return f"Failed to close tab: {tab_id}"


@tool
def list_open_tabs() -> str:
    """Lists tracked open tabs so the agent can inspect and switch between them."""
    tabs = []
    for tab_id, tab in _tabs.items():
        tabs.append(
            {
                "tab_id": tab_id,
                "url": tab.url,
                "active": tab.active,
                "history_length": len(tab.history),
                "window_handle_known": bool(tab.window_handle),
            }
        )

    return json.dumps(
        {
            "current_tab_id": _current_tab_id,
            "tabs": tabs,
        },
        indent=2,
    )


@tool
def find_path_to_target(target: str, keyword_values: str = None) -> str:
    """Use depth-1 scout interaction to find best URL for target.
    
    Args:
        target: Target description to search for
        keyword_values: Optional JSON string with keyword weights
    """
    from smolclaw.agent.interactions.scout.FindPathToTarget import FindPathToTarget

    result = FindPathToTarget.execute(target, keyword_values)
    if result.error:
        return json.dumps(
            {
                "error": result.error,
                "logs": result.logs,
                "top_links_checked": result.top_links_checked,
            },
            indent=2,
        )

    return json.dumps(
        {
            "best_url": result.best_url,
            "confidence_score": result.confidence_score,
            "reason": result.reason,
            "logs": result.logs,
        },
        indent=2,
    )


@tool
def get_address() -> str:
    """Get address information from browser and host."""
    from smolclaw.agent.interactions.location.GetAddress import GetAddress

    recovery_note = _recover_live_page("get_address")
    address = GetAddress.execute()
    payload = json.dumps(
        {
            "current_page_url": address.current_page_url,
            "system_hostname": address.system_hostname,
            "local_ip_address": address.local_ip_address,
            "browser_title": address.browser_title,
        },
        indent=2,
    )
    if recovery_note:
        return f"{recovery_note}\n{payload}"
    return payload


@tool
def get_geolocation() -> str:
    """Gets geolocation information from browser geolocation API."""
    from smolclaw.agent.interactions.location.GetGeoLocation import GetGeoLocation

    geo = GetGeoLocation.execute()
    return json.dumps(
        {
            "latitude": geo.latitude,
            "longitude": geo.longitude,
            "accuracy": geo.accuracy,
            "altitude": geo.altitude,
            "heading": geo.heading,
            "speed": geo.speed,
            "success": geo.success,
            "error": geo.error,
        },
        indent=2,
    )


@tool
def quit_browser() -> str:
    """Safely quits the browser and returns a confirmation string."""
    from smolclaw.agent.interactions.browser.Quit import QuitBrowser

    browser = Browser()
    browser.is_running = True
    return QuitBrowser.execute(browser)


@tool
def think(query: str) -> str:
    """Call the cognitive strategy interaction.
    
    Args:
        query: Query or topic to think about
    """
    from smolclaw.agent.interactions.thinking.Think import Think

    return Think.execute(query)


@tool
def search_item_ctrl_f(text: str, nth_result: int = 1) -> str:
    """Search for text on page and focus the nth match.
    
    Args:
        text: Text to search for
        nth_result: Which match to focus (1-based)
    """
    from smolclaw.agent.interactions.navigation.SearchOnPage import SearchOnPage

    recovery_note = _recover_live_page("search_item_ctrl_f")
    result = SearchOnPage.execute(text, nth_result)
    if recovery_note:
        return f"{recovery_note}\n{result}"
    return result


@tool
def go_back() -> str:
    """Go back to previous page using shared navigation stack."""
    from smolclaw.agent.interactions.navigation.GoBack import GoBack

    return GoBack.execute(_navigation_stack)


@tool
def close_popups() -> str:
    """Close visible modal/popups via ESC key."""
    from smolclaw.agent.interactions.navigation.ClosePopups import ClosePopups

    return ClosePopups.execute()


class ToolRegistry:
    """Central registry for all available tools."""

    @staticmethod
    def get_all_tools():
        """Returns all registered tools for the agent."""
        return _registry_tools()

    @staticmethod
    def get_tool_names():
        """Returns names of all registered tools."""
        return [_tool_name(t) for t in _registry_tools()]
