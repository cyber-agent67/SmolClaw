"""Unregister browser interaction."""

from agentic_navigator.entities.browser.BrowserRegistry import BrowserRegistry


class UnregisterBrowser:
    @staticmethod
    def execute(registry: BrowserRegistry, browser) -> BrowserRegistry:
        if browser in registry.active_browsers:
            registry.active_browsers.remove(browser)
        return registry
