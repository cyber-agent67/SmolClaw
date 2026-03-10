"""Close all browsers interaction."""

import helium

from agentic_navigator.entities.browser.BrowserRegistry import BrowserRegistry


class CloseAllBrowsers:
    @staticmethod
    def execute(registry: BrowserRegistry) -> None:
        for browser in registry.active_browsers[:]:
            try:
                if browser:
                    helium.kill_browser()
            except Exception:
                pass
        registry.active_browsers.clear()
