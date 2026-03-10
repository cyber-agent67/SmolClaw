"""Switch tab interaction."""

from typing import Dict

from helium import go_to
from helium import get_driver

from agentic_navigator.entities.browser.Tab import Tab


class SwitchTab:
    @staticmethod
    def execute(tabs: Dict[str, Tab], tab_id: str) -> bool:
        """Switches to a specific tab by ID."""
        tab = tabs.get(tab_id)
        if tab is None:
            return False

        try:
            driver = get_driver()
            if tab.window_handle and tab.window_handle in driver.window_handles:
                driver.switch_to.window(tab.window_handle)
                tab.window_handle = driver.current_window_handle
                return True
        except Exception:
            pass

        if tab.url:
            go_to(tab.url)
            try:
                driver = get_driver()
                tab.window_handle = driver.current_window_handle
                tab.url = driver.current_url
            except Exception:
                pass
            return True

        return False
