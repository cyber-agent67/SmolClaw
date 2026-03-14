"""Capture page state interaction."""

import base64
from datetime import datetime

import helium

from smolclaw.agent.entities.browser.PageState import PageState


class CapturePageState:
    @staticmethod
    def execute() -> PageState:
        state = PageState()
        driver = helium.get_driver()

        state.url = driver.current_url
        state.title = driver.title
        state.dom_html = driver.page_source
        state.timestamp = datetime.utcnow().isoformat() + "Z"

        png_bytes = driver.get_screenshot_as_png()
        state.screenshot_base64 = base64.b64encode(png_bytes).decode("ascii")
        state.viewport_width = driver.execute_script("return window.innerWidth")
        state.viewport_height = driver.execute_script("return window.innerHeight")
        return state
