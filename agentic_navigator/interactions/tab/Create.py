"""Create tab interaction."""

from typing import Dict, Optional, Tuple

import helium
from helium import get_driver

from agentic_navigator.entities.browser.Tab import Tab


class CreateTab:
    @staticmethod
    def execute(tabs: Dict[str, Tab], tab_counter: int, url: Optional[str] = None) -> Tuple[Tab, int, str]:
        """Creates a new browser tab and optionally navigates to a URL."""
        tab_counter += 1
        tab_id = f"tab_{tab_counter}"

        tab = Tab()
        tab.id = tab_id
        tab.url = None
        tab.history = []
        tab.active = True

        tabs[tab_id] = tab

        try:
            driver = get_driver()
            existing_handles = list(driver.window_handles)
            driver.execute_script("window.open('about:blank', '_blank');")
            new_handles = [handle for handle in driver.window_handles if handle not in existing_handles]
            if new_handles:
                driver.switch_to.window(new_handles[-1])
            tab.window_handle = driver.current_window_handle
        except Exception:
            tab.window_handle = None

        if url:
            helium.go_to(url)
            try:
                driver = get_driver()
                tab.url = driver.current_url
                tab.window_handle = driver.current_window_handle
            except Exception:
                tab.url = url
            tab.history = [tab.url] if tab.url else [url]

        return tab, tab_counter, tab_id
