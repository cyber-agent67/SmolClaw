"""Initialize browser interaction."""

import helium
from selenium import webdriver

from smolclaw.agent.config.BrowserConfig import BrowserConfig
from smolclaw.agent.entities.browser.Browser import Browser


class InitializeBrowser:
    @staticmethod
    def execute(config: BrowserConfig = None) -> Browser:
        """Initializes a new browser instance with chrome options."""
        if config is None:
            config = BrowserConfig()

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f"--force-device-scale-factor={config.scale_factor}")
        chrome_options.add_argument(f"--window-size={config.window_width},{config.window_height}")
        chrome_options.add_argument("--disable-pdf-viewer")
        chrome_options.add_argument(f"--window-position={config.window_x},{config.window_y}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        browser = Browser()
        browser.driver = helium.start_chrome(headless=config.headless, options=chrome_options)
        browser.is_running = True
        browser.headless = config.headless

        return browser
