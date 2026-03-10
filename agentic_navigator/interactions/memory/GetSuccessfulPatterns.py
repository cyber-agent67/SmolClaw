"""Get successful patterns interaction."""

from typing import List

from agentic_navigator.entities.memory.Experience import Experience
from agentic_navigator.entities.memory.ExperienceMemory import ExperienceMemory


class GetSuccessfulPatterns:
    @staticmethod
    def execute(memory: ExperienceMemory, task_description: str) -> List[Experience]:
        """Retrieves successful navigation patterns for similar tasks."""
        patterns = []
        for exp in memory.experiences:
            if exp.task == task_description and exp.success:
                patterns.append(exp)
        return patterns
