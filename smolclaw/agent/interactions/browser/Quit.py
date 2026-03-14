"""Quit browser interaction."""

import helium

from smolclaw.agent.entities.browser.Browser import Browser


class QuitBrowser:
    @staticmethod
    def execute(browser: Browser) -> str:
        """Safely quits the browser."""
        try:
            helium.kill_browser()
            browser.is_running = False
            browser.driver = None
            return (
                "[Browser Quit]: Browser has been successfully closed. "
                "To finish the task, you MUST now output a code block "
                "with your final answer."
            )
        except Exception as e:
            return f"[Browser Quit]: Error closing browser - {str(e)}"
