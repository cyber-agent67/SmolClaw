"""Agent entity - pure state container."""

from typing import Any


class Agent:
    def __init__(self):
        self.code_agent: Any = None
        self.model: Any = None
        self.max_steps: int = 20
        self.verbosity_level: int = 2
