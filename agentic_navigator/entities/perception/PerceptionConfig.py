"""PerceptionConfig entity - configuration for perception layer."""


class PerceptionConfig:
    def __init__(self):
        self.florence_model_id: str = "microsoft/Florence-2-large"
        self.florence_device: str = "cuda"
        self.florence_dtype: str = "float16"
        self.use_florence: bool = True
        self.use_ocr: bool = True
        self.use_object_detection: bool = True
        self.use_grounding: bool = True
        self.max_dom_elements: int = 500
        self.screenshot_max_width: int = 1000
        self.screenshot_max_height: int = 1350
        self.element_visibility_threshold: float = 0.5
