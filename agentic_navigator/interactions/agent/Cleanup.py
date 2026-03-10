"""Cleanup agent resources interaction."""

from agentic_navigator.entities.browser.Browser import Browser
from agentic_navigator.interactions.browser.Quit import QuitBrowser


class CleanupAgent:
    @staticmethod
    def execute(browser: Browser) -> None:
        """Cleans up browser resources when agent finishes."""
        try:
            if browser and browser.is_running:
                QuitBrowser.execute(browser)
        except Exception:
            pass
