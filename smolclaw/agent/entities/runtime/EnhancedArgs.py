"""EnhancedArgs entity - pure state container."""

from typing import Optional


class EnhancedArgs:
    def __init__(self):
        self.url: str = "https://www.google.com"
        self.prompt: Optional[str] = None
        self.output: str = "data/output.json"
        self.model_type: str = "LiteLLMModel"
        self.model_id: str = "gpt-4o"
