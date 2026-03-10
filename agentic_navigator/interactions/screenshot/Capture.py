"""Capture screenshot interaction."""

from io import BytesIO
from time import sleep

import helium
from PIL import Image
from smolagents import CodeAgent
from smolagents.agents import ActionStep

from agentic_navigator.entities.browser.Screenshot import Screenshot


class CaptureScreenshot:
    @staticmethod
    def execute(memory_step: ActionStep, agent: CodeAgent) -> Screenshot:
        """Captures a screenshot of the current browser state."""
        screenshot = Screenshot()
        sleep(1.0)

        try:
            driver = helium.get_driver()
            current_step = memory_step.step_number
            screenshot.step_number = current_step

            if driver is not None:
                for prev_step in agent.memory.steps:
                    if isinstance(prev_step, ActionStep) and prev_step.step_number <= current_step - 2:
                        prev_step.observations_images = None

                png_bytes = driver.get_screenshot_as_png()
                image = Image.open(BytesIO(png_bytes))
                screenshot.image = image.copy()
                screenshot.size = image.size
                screenshot.url_at_capture = driver.current_url

                print(f"Captured a browser screenshot: {image.size} pixels")
                memory_step.observations_images = [image.copy()]

            url_info = f"Current url: {driver.current_url}" if driver is not None else "Current url: Driver closed"
            memory_step.observations = url_info if memory_step.observations is None else memory_step.observations + "\n" + url_info

        except Exception:
            url_info = "Current url: Unable to access driver"
            memory_step.observations = url_info if memory_step.observations is None else memory_step.observations + "\n" + url_info

        return screenshot
