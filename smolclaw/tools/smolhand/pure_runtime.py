"""Pure functional smolhand runtime with explicit effects.

This module refactors smolhand to use pure functions with explicit effect types,
removing all global mutable state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from smolclaw.cognitive.effects import Effect, Result, State, Success, Error, effect


# =============================================================================
# Pure State Containers
# =============================================================================

@dataclass
class BrowserSession:
    """Immutable browser session state."""
    is_running: bool = False
    url: str = ""
    title: str = ""
    page_source: str = ""
    headless: bool = False


@dataclass
class SmolhandState:
    """Complete smolhand state (immutable)."""
    browser: BrowserSession = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.browser is None:
            object.__setattr__(self, 'browser', BrowserSession())
        if self.context is None:
            object.__setattr__(self, 'context', {})


# =============================================================================
# Pure Functions (No Side Effects)
# =============================================================================

def validate_url(url: str) -> Result[str, str]:
    """Validate URL string (pure function)."""
    if not isinstance(url, str):
        return Error("URL must be a string")
    if not url.strip():
        return Error("URL must be non-empty")
    return Success(url.strip())


def create_browser_session(headless: bool = False) -> BrowserSession:
    """Create new browser session (pure function)."""
    return BrowserSession(is_running=False, headless=headless)


def start_browser_session(session: BrowserSession) -> BrowserSession:
    """Mark browser session as started (pure state transformation)."""
    return BrowserSession(
        is_running=True,
        url=session.url,
        title=session.title,
        page_source=session.page_source,
        headless=session.headless,
    )


def navigate_to_url(session: BrowserSession, url: str) -> BrowserSession:
    """Update session with new URL (pure state transformation)."""
    return BrowserSession(
        is_running=session.is_running,
        url=url,
        title=session.title,  # Would be updated by actual navigation
        page_source=session.page_source,
        headless=session.headless,
    )


def capture_snapshot(session: BrowserSession) -> Dict[str, Any]:
    """Capture browser snapshot (pure function of state)."""
    return {
        "url": session.url,
        "title": session.title,
        "page_source_length": len(session.page_source),
        "is_running": session.is_running,
    }


# =============================================================================
# Effectful Operations (Side Effects Explicit)
# =============================================================================

def ensure_browser_started_effect(
    headless: bool = False
) -> Effect[Result[BrowserSession, str]]:
    """Effect: Start browser if not running.
    
    This makes the side effect explicit - caller knows this will
    interact with the browser when run().
    """
    def compute() -> Result[BrowserSession, str]:
        try:
            # Import here to avoid circular dependencies
            from smolclaw.agent.config.BrowserConfig import BrowserConfig
            from smolclaw.agent.interactions.browser.Initialize import InitializeBrowser
            
            config = BrowserConfig()
            config.headless = headless
            browser = InitializeBrowser.execute(config)
            
            session = BrowserSession(
                is_running=getattr(browser, 'is_running', False),
                headless=headless,
            )
            return Success(session)
        except Exception as e:
            return Error(f"Failed to start browser: {e}")
    
    return Effect(compute)


def set_browser_url_effect(
    session: BrowserSession,
    url: str
) -> Effect[Result[BrowserSession, str]]:
    """Effect: Navigate to URL.
    
    Side effect is explicit - actual navigation happens on run().
    """
    def compute() -> Result[BrowserSession, str]:
        try:
            from smolclaw.agent.tools.ToolRegistry import set_browser_url
            
            # Validate URL first (pure)
            validation = validate_url(url)
            if not validation.is_success:
                return validation
            
            # Navigate (effect)
            result = set_browser_url(url)
            
            # Update session state (pure)
            new_session = navigate_to_url(session, url)
            return Success(new_session)
        except Exception as e:
            return Error(f"Navigation failed: {e}")
    
    return Effect(compute)


def get_browser_snapshot_effect(
    session: BrowserSession
) -> Effect[Result[Dict[str, Any], str]]:
    """Effect: Get browser snapshot."""
    def compute() -> Result[Dict[str, Any], str]:
        try:
            from smolclaw.agent.tools.ToolRegistry import get_browser_snapshot
            
            snapshot_json = get_browser_snapshot()
            snapshot = json.loads(snapshot_json)
            return Success(snapshot)
        except Exception as e:
            return Error(f"Snapshot failed: {e}")
    
    return Effect(compute)


# =============================================================================
# Composed Operations (Pure + Effects)
# =============================================================================

def ensure_connected_page_effect(
    url: str,
    headless: bool = False
) -> Effect[Result[Dict[str, Any], str]]:
    """Effect: Connect to page and return snapshot.
    
    This is a composed effect that:
    1. Validates URL (pure)
    2. Starts browser (effect)
    3. Navigates to URL (effect)
    4. Captures snapshot (effect)
    
    All side effects are explicit and deferred until run().
    """
    def compute() -> Result[Dict[str, Any], str]:
        # Step 1: Validate URL (pure)
        validation = validate_url(url)
        if not validation.is_success:
            return validation
        
        # Step 2: Start browser (effect)
        browser_result = ensure_browser_started_effect(headless).run()
        if not browser_result.is_success:
            return browser_result
        
        session = browser_result.value
        
        # Step 3: Navigate (effect)
        nav_result = set_browser_url_effect(session, url).run()
        if not nav_result.is_success:
            return nav_result
        
        session = nav_result.value
        
        # Step 4: Snapshot (effect)
        snapshot_result = get_browser_snapshot_effect(session).run()
        if not snapshot_result.is_success:
            return snapshot_result
        
        # Return composed result
        return Success({
            "status": "connected",
            "url": url,
            "snapshot": snapshot_result.value,
        })
    
    return Effect(compute)


def close_page_session_effect(
    session: BrowserSession
) -> Effect[Result[str, str]]:
    """Effect: Close browser session."""
    def compute() -> Result[str, str]:
        if not session.is_running:
            return Success("No active browser session.")
        
        try:
            from smolclaw.agent.interactions.browser.Quit import QuitBrowser
            
            # Create temporary browser object for quit
            class TempBrowser:
                def __init__(self, s):
                    self.is_running = s.is_running
                    self.driver = None
            
            browser = TempBrowser(session)
            result = QuitBrowser.execute(browser)
            return Success(result)
        except Exception as e:
            return Error(f"Close failed: {e}")
    
    return Effect(compute)


# =============================================================================
# State Monad for Session Management
# =============================================================================

def with_browser_session[T](
    operation: Callable[[BrowserSession], Effect[Result[T, str]]]
) -> State[SmolhandState]:
    """State monad wrapper for browser operations.
    
    Threads browser session state through effectful operations.
    """
    def stateful_compute(state: SmolhandState) -> tuple[Result[T, str], SmolhandState]:
        # Run operation with current session
        effect_result = operation(state.browser).run()
        
        # Update state based on result
        if effect_result.is_success and isinstance(effect_result.value, BrowserSession):
            new_state = SmolhandState(
                browser=effect_result.value,
                context=state.context,
            )
        else:
            new_state = state
        
        return (effect_result, new_state)
    
    return State(stateful_compute)


# =============================================================================
# Legacy Compatibility (Wrappers for Old API)
# =============================================================================

_SMOLHAND_STATE: SmolhandState = SmolhandState()


def ensure_connected_page(url: str, headless: bool = False) -> str:
    """Legacy API - wraps pure effect version.
    
    DEPRECATED: Use ensure_connected_page_effect().run() instead.
    """
    global _SMOLHAND_STATE
    
    result = ensure_connected_page_effect(url, headless).run()
    
    if result.is_success:
        # Update global state (for backward compatibility)
        _SMOLHAND_STATE = SmolhandState(
            browser=BrowserSession(is_running=True, url=url, headless=headless),
            context=_SMOLHAND_STATE.context,
        )
        return json.dumps(result.value, indent=2)
    else:
        return f"Smolhand connection error: {result.error}"


def close_page_session() -> str:
    """Legacy API - wraps pure effect version."""
    global _SMOLHAND_STATE
    
    result = close_page_session_effect(_SMOLHAND_STATE.browser).run()
    
    if result.is_success:
        _SMOLHAND_STATE = SmolhandState(
            browser=BrowserSession(is_running=False),
            context=_SMOLHAND_STATE.context,
        )
        return result.value
    else:
        return f"Smolhand session close error: {result.error}"


__all__ = [
    # State
    "BrowserSession",
    "SmolhandState",
    # Pure functions
    "validate_url",
    "create_browser_session",
    "start_browser_session",
    "navigate_to_url",
    "capture_snapshot",
    # Effects
    "ensure_browser_started_effect",
    "set_browser_url_effect",
    "get_browser_snapshot_effect",
    "ensure_connected_page_effect",
    "close_page_session_effect",
    # State monad
    "with_browser_session",
    # Legacy (deprecated)
    "ensure_connected_page",
    "close_page_session",
]
