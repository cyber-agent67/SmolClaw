"""Browser entity - pure state container."""


class Browser:
    def __init__(self):
        self.driver = None
        self.is_running: bool = False
        self.headless: bool = False
