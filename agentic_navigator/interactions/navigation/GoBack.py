"""Go back navigation interaction."""

from helium import get_driver, go_to

from agentic_navigator.entities.browser.NavigationStack import NavigationStack


class GoBack:
    @staticmethod
    def execute(navigation_stack: NavigationStack) -> str:
        """Navigates back to the previous page."""
        if len(navigation_stack.stack) > 1:
            navigation_stack.stack.pop()
            if navigation_stack.stack:
                previous_url = navigation_stack.stack[-1]
                go_to(previous_url)
                return f"Returned to previous page: {previous_url}"

        driver = get_driver()
        driver.back()
        return "Navigated back using browser history"
