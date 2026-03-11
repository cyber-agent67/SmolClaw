"""Load experiences interaction."""

from smolclaw.agent.entities.memory.ExperienceMemory import ExperienceMemory
from smolclaw.agent.repositories.ExperienceRepository import ExperienceRepository


class LoadExperiences:
    @staticmethod
    def execute(memory: ExperienceMemory) -> ExperienceMemory:
        """Loads experiences from persistent storage into memory."""
        memory.experiences = ExperienceRepository.load(memory.memory_file)
        return memory
