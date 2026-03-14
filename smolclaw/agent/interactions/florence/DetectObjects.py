"""Detect objects interaction."""

from smolclaw.agent.entities.perception.VisualDescription import VisualDescription
from smolclaw.agent.interactions.perception.ImageAnalysis import summarize_image


class DetectObjects:
    @staticmethod
    def execute(image_base64: str) -> VisualDescription:
        desc = VisualDescription()
        summary = summarize_image(image_base64)
        if summary:
            desc.detailed_caption = (
                f"Heuristic image analysis for a {summary['orientation']} frame {summary['width']}x{summary['height']}. "
                f"{summary['detailed_caption']}"
            )
            desc.region_descriptions = summary["region_descriptions"]
            desc.raw_florence_output = {
                "analysis": "heuristic-region-scan",
                "detected_objects": 0,
                "reason": "No Florence object model was invoked; returning region-level analysis instead.",
            }
        return desc
