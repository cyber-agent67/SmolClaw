"""ExperienceMemory entity - pure state container."""

from typing import List

from smolclaw.agent.entities.memory.Experience import Experience


class ExperienceMemory:
    def __init__(self):
        self.memory_file: str = "navigation_missions.json"
        self.experiences: List[Experience] = []
