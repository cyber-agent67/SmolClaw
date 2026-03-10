"""ExperienceMemory entity - pure state container."""

from typing import List

from agentic_navigator.entities.memory.Experience import Experience


class ExperienceMemory:
    def __init__(self):
        self.memory_file: str = "navigation_missions.json"
        self.experiences: List[Experience] = []
