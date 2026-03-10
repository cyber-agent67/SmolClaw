"""Close tab interaction."""

from typing import Dict, Optional, Tuple

from helium import get_driver

from agentic_navigator.entities.browser.Tab import Tab


class CloseTab:
    @staticmethod
    def execute(tabs: Dict[str, Tab], tab_id: str, current_tab_id: str) -> Tuple[bool, Optional[str]]:
        """Closes a specific tab."""
        tab = tabs.get(tab_id)
        if tab is None:
            return False, current_tab_id

        fallback_handle = None
        try:
            driver = get_driver()
            if tab.window_handle and tab.window_handle in driver.window_handles:
                remaining_handles = [handle for handle in driver.window_handles if handle != tab.window_handle]
                driver.switch_to.window(tab.window_handle)
                driver.close()
                if remaining_handles:
                    driver.switch_to.window(remaining_handles[0])
                    fallback_handle = driver.current_window_handle
        except Exception:
            fallback_handle = None

        del tabs[tab_id]

        new_current = current_tab_id
        if current_tab_id == tab_id:
            if fallback_handle:
                for candidate_id, candidate_tab in tabs.items():
                    if candidate_tab.window_handle == fallback_handle:
                        new_current = candidate_id
                        break
                else:
                    available = list(tabs.keys())
                    new_current = available[0] if available else None
            else:
                available = list(tabs.keys())
                new_current = available[0] if available else None

        return True, new_current
