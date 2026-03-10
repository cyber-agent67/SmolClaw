"""Caption image interaction."""

from agentic_navigator.entities.perception.VisualDescription import VisualDescription
from agentic_navigator.interactions.perception.ImageAnalysis import summarize_image


class CaptionImage:
    @staticmethod
    def execute(image_base64: str) -> VisualDescription:
        desc = VisualDescription()
        summary = summarize_image(image_base64)
        if summary:
            desc.caption = summary["caption"]
            desc.detailed_caption = summary["detailed_caption"]
            desc.region_descriptions = summary["region_descriptions"]
            desc.raw_florence_output = {
                "analysis": "heuristic-caption",
                "orientation": summary["orientation"],
                "brightness": summary["brightness"],
            }
        return desc
