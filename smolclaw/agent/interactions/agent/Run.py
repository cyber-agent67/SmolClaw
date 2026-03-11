"""Run agent interaction — now with token-optimized memory injection."""

import helium
from helium import get_driver

from smolclaw.agent.entities.runtime.Agent import Agent
from smolclaw.agent.entities.memory.Experience import Experience
from smolclaw.agent.entities.memory.ExperienceMemory import ExperienceMemory
from smolclaw.agent.entities.browser.NavigationStack import NavigationStack
from smolclaw.agent.config.MemoryConfig import MemoryConfig
from smolclaw.agent.interactions.memory.SaveExperience import SaveExperience
from smolclaw.agent.interactions.memory_optimization.InjectMemory import InjectMemory


class RunAgent:
    @staticmethod
    def execute(
        agent: Agent,
        prompt: str,
        start_url: str,
        experience_memory: ExperienceMemory,
        navigation_stack: NavigationStack,
    ) -> str:
        """
        Runs the agent with token-optimized memory injection.
        
        BEFORE (old approach):
            Dump all experiences into prompt = 100K tokens
        
        AFTER (new approach):
            Token-optimized injection = ~2K tokens
        
        50x token reduction.
        
        Args:
            agent: Initialized Agent entity
            prompt: User's task prompt
            start_url: Starting URL
            experience_memory: Memory of past experiences
            navigation_stack: Navigation history
        
        Returns:
            Agent execution result
        """
        # Navigate to start URL
        navigation_stack.stack = [start_url]
        helium.go_to(start_url)
        
        # =====================================================================
        # TOKEN-OPTIMIZED MEMORY INJECTION
        # =====================================================================
        
        # Get experiences from memory
        experiences = experience_memory.experiences if hasattr(experience_memory, 'experiences') else []
        
        # Inject memory (2K tokens instead of 100K)
        memory_injection = InjectMemory.execute(
            experiences=experiences,
            current_goal=prompt,
            config=MemoryConfig(),
            max_tokens=2000
        )
        
        # Build enhanced prompt WITH memory
        if memory_injection:
            enhanced_prompt = f"{memory_injection}\n\n---\n\n{prompt}"
        else:
            enhanced_prompt = prompt
        
        # =====================================================================
        # EXECUTE AGENT
        # =====================================================================
        
        agent.code_agent.python_executor("from helium import *")
        result = agent.code_agent.run(enhanced_prompt)
        
        # =====================================================================
        # SAVE EXPERIENCE
        # =====================================================================
        
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
