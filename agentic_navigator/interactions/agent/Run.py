"""Run agent interaction."""

import helium
from helium import get_driver

from agentic_navigator.entities.runtime.Agent import Agent
from agentic_navigator.entities.memory.Experience import Experience
from agentic_navigator.entities.memory.ExperienceMemory import ExperienceMemory
from agentic_navigator.entities.browser.NavigationStack import NavigationStack
from agentic_navigator.interactions.memory.FindSimilarExperiences import FindSimilarExperiences
from agentic_navigator.interactions.memory.SaveExperience import SaveExperience


class RunAgent:
    @staticmethod
    def execute(
        agent: Agent,
        prompt: str,
        start_url: str,
        experience_memory: ExperienceMemory,
        navigation_stack: NavigationStack,
    ) -> str:
        """Runs the agent with an enhanced prompt and saves experience."""
        navigation_stack.stack = [start_url]
        helium.go_to(start_url)

        similar = FindSimilarExperiences.execute(experience_memory, prompt)

        experience_context = ""
        if similar:
            experience_context = "Past successful experiences for similar tasks:\n"
            for exp in similar:
                if exp.success:
                    experience_context += f"- Task: {exp.task}\n"
                    experience_context += f"- Result: {exp.result or 'Success'}\n"

        enhanced_prompt = f"{experience_context}\n\n{prompt}"

        agent.code_agent.python_executor("from helium import *")
        result = agent.code_agent.run(enhanced_prompt)

        final_url = "unknown"
        try:
            driver = get_driver()
            if driver:
                final_url = driver.current_url
        except Exception:
            pass

        experience = Experience()
        experience.task = prompt
        experience.start_url = start_url
        experience.context = enhanced_prompt
        experience.actions = []
        experience.success = True
        experience.final_url = final_url
        experience.result = str(result) if result else "No result"

        SaveExperience.execute(experience_memory, experience)
        return result
