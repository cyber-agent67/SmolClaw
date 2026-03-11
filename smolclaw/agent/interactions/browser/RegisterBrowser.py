"""Register browser interaction."""

from smolclaw.agent.entities.browser.BrowserRegistry import BrowserRegistry


class RegisterBrowser:
    @staticmethod
    def execute(registry: BrowserRegistry, browser) -> BrowserRegistry:
        if browser not in registry.active_browsers:
            registry.active_browsers.append(browser)
        return registry
