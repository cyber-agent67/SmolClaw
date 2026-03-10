"""Find similar experiences interaction."""

from typing import List

from agentic_navigator.entities.memory.Experience import Experience
from agentic_navigator.entities.memory.ExperienceMemory import ExperienceMemory


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
