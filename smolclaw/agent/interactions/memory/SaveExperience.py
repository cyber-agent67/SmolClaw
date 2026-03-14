"""Save experience interaction."""

from datetime import datetime

from smolclaw.agent.entities.memory.Experience import Experience
from smolclaw.agent.entities.memory.ExperienceMemory import ExperienceMemory
from smolclaw.agent.repositories.ExperienceRepository import ExperienceRepository


class SaveExperience:
    @staticmethod
    def execute(memory: ExperienceMemory, experience: Experience) -> ExperienceMemory:
        """Saves a new experience to memory and persists it."""
        experience.timestamp = datetime.now().isoformat()
        memory.experiences.append(experience)
        ExperienceRepository.save(memory.memory_file, memory.experiences)
        return memory
