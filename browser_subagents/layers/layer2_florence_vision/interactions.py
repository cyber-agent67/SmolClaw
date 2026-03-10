"""Interactions for Layer 2 (screenshot + Florence bridge)."""

from __future__ import annotations

from agentic_navigator.interactions.perception.CapturePageState import CapturePageState
from agentic_navigator.interactions.perception.DescribeScreenshot import DescribeScreenshot
from browser_subagents.layers.layer2_florence_vision.entities import VisionContextEntity


class BuildVisionContext:
    @staticmethod
    def execute(prompt_hint: str = "") -> VisionContextEntity:
        state = CapturePageState.execute()

        florence_status = "not-invoked"
        try:
            from agentic_navigator.interactions.florence.LoadModel import LoadFlorenceModel

            LoadFlorenceModel.execute()
            florence_status = "loaded"
        except Exception as exc:
            florence_status = f"unavailable: {exc}"

        visual = DescribeScreenshot.execute(state.screenshot_base64)
        return VisionContextEntity(
            prompt_hint=prompt_hint,
            url=state.url,
            title=state.title,
            florence_status=florence_status,
            visual_caption=visual.caption,
            visual_detail=visual.detailed_caption,
            regions=visual.region_descriptions,
        )
