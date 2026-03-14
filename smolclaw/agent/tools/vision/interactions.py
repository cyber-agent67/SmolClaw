"""Vision analysis operations for AI Agent visual understanding.

This module provides Florence-2 vision analysis logic used by the AI Agent
to understand visual content of web pages.
"""

from __future__ import annotations

from smolclaw.agent.interactions.perception.CapturePageState import CapturePageState
from smolclaw.agent.interactions.perception.DescribeScreenshot import DescribeScreenshot
from smolclaw.agent.tools.vision.entities import VisionContextEntity


class BuildVisionContext:
    """Builds visual context by capturing screenshot and analyzing with Florence-2."""

    @staticmethod
    def execute(prompt_hint: str = "") -> VisionContextEntity:
        """
        Execute vision analysis and return visual context.

        Args:
            prompt_hint: Optional hint to guide the visual analysis

        Returns:
            VisionContextEntity with Florence-2 analysis results
        """
        state = CapturePageState.execute()

        florence_status = "not-invoked"
        try:
            from smolclaw.agent.interactions.florence.LoadModel import LoadFlorenceModel

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


__all__ = ["BuildVisionContext"]
