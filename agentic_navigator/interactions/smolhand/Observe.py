"""Observe interaction for smolhand runloop."""

from agentic_navigator.interactions.perception.CapturePageState import CapturePageState
from agentic_navigator.interactions.perception.DescribeDOM import DescribeDOM
from agentic_navigator.interactions.perception.DescribeScreenshot import DescribeScreenshot
from agentic_navigator.interactions.perception.MergeDescriptions import MergeDescriptions


class SmolhandObserve:
    @staticmethod
    def execute() -> str:
        state = CapturePageState.execute()
        visual = DescribeScreenshot.execute(state.screenshot_base64)
        dom = DescribeDOM.execute(state.dom_html, state.url)
        merged = MergeDescriptions.execute(visual, dom)
        return merged.merged_description
