"""Browser configuration entity."""


class BrowserConfig:
    def __init__(self):
        self.scale_factor: float = 1
        self.window_width: int = 1000
        self.window_height: int = 1350
        self.window_x: int = 0
        self.window_y: int = 0
        self.headless: bool = False
