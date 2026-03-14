"""Memory operations — load, save, query experiences and prompt cache."""

from datetime import datetime
from typing import List

from core.memory.store import Experience, ExperienceMemory
from agentic_navigator.repositories.ExperienceRepository import ExperienceRepository


class LoadExperiences:
    @staticmethod
    def execute(memory: ExperienceMemory) -> ExperienceMemory:
        """Loads experiences from persistent storage into memory."""
        memory.experiences = ExperienceRepository.load(memory.memory_file)
        return memory


class SaveExperience:
    @staticmethod
    def execute(memory: ExperienceMemory, experience: Experience) -> ExperienceMemory:
        """Saves a new experience to memory and persists it."""
        experience.timestamp = datetime.now().isoformat()
        memory.experiences.append(experience)
        ExperienceRepository.save(memory.memory_file, memory.experiences)
        return memory


class FindSimilarExperiences:
    @staticmethod
    def execute(memory: ExperienceMemory, current_context: str, limit: int = 5) -> List[Experience]:
        """Finds similar past experiences based on keyword matching."""
        similar = []
        context_lower = current_context.lower()
        keywords = context_lower.split()[:5]

        for exp in memory.experiences:
            exp_context = exp.context.lower()
            if any(keyword in exp_context for keyword in keywords):
                similar.append(exp)

        return similar[-limit:]


class GetSuccessfulPatterns:
    @staticmethod
    def execute(memory: ExperienceMemory, task_description: str) -> List[Experience]:
        """Retrieves successful navigation patterns for similar tasks."""
        return [exp for exp in memory.experiences if exp.task == task_description and exp.success]
