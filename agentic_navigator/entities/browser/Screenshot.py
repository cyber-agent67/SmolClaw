"""Screenshot entity - pure state container."""

from typing import Optional, Tuple

from PIL import Image


class Screenshot:
    def __init__(self):
        self.image: Optional[Image.Image] = None
        self.step_number: int = 0
        self.url_at_capture: str = ""
        self.size: Tuple[int, int] = (0, 0)
