"""VisualDescription entity - vision model output."""

from typing import Any, Dict, List, Optional


class BoundingBox:
    def __init__(self):
        self.x1: float = 0.0
        self.y1: float = 0.0
        self.x2: float = 0.0
        self.y2: float = 0.0
        self.label: str = ""
        self.confidence: float = 0.0


class VisualDescription:
    def __init__(self):
        self.caption: str = ""
        self.detailed_caption: str = ""
        self.ocr_text: List[Dict[str, Any]] = []
        self.detected_objects: List[BoundingBox] = []
        self.grounded_elements: List[Dict[str, Any]] = []
        self.region_descriptions: List[Dict[str, Any]] = []
        self.raw_florence_output: Optional[Any] = None
