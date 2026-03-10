"""Navigate to URL interaction."""

import helium
from helium import get_driver

from agentic_navigator.entities.browser.NavigationStack import NavigationStack
from agentic_navigator.entities.browser.Tab import Tab


class GoToURL:
    @staticmethod
    def execute(url: str, navigation_stack: NavigationStack, current_tab: Tab = None) -> str:
        """Navigates the browser to a specific URL."""
        driver = get_driver()
        current_url = driver.current_url

        if not navigation_stack.stack or navigation_stack.stack[-1] != current_url:
            navigation_stack.stack.append(current_url)

        helium.go_to(url)

        driver = get_driver()
        new_url = driver.current_url

        if current_tab:
            current_tab.url = new_url
            current_tab.history.append(new_url)

        return f"Successfully navigated to: {new_url}"
