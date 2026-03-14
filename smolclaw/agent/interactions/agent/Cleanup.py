"""Cleanup agent resources interaction."""

from smolclaw.agent.entities.browser.Browser import Browser
from smolclaw.agent.interactions.browser.Quit import QuitBrowser


class CleanupAgent:
    @staticmethod
    def execute(browser: Browser) -> None:
        """Cleans up browser resources when agent finishes."""
        try:
            if browser and browser.is_running:
                QuitBrowser.execute(browser)
        except Exception:
            pass
