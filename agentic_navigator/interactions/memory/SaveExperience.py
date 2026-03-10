"""Save experience interaction."""

from datetime import datetime

from agentic_navigator.entities.memory.Experience import Experience
from agentic_navigator.entities.memory.ExperienceMemory import ExperienceMemory
from agentic_navigator.repositories.ExperienceRepository import ExperienceRepository


class SaveExperience:
    @staticmethod
    def execute(memory: ExperienceMemory, experience: Experience) -> ExperienceMemory:
        """Saves a new experience to memory and persists it."""
        experience.timestamp = datetime.now().isoformat()
        memory.experiences.append(experience)
        ExperienceRepository.save(memory.memory_file, memory.experiences)
        return memory
