"""Refine prompt interaction."""

import re

from smolclaw.agent.entities.memory.PromptCache import PromptCache


class RefinePrompt:
    @staticmethod
    def bag_of_words(prompt: str) -> str:
        cleaned = re.sub(r"[^\w\s]", "", prompt.lower())
        words = sorted(list(set(cleaned.split())))
        return " ".join(words)

    @staticmethod
    def execute(raw_prompt: str, prompt_cache: PromptCache) -> str:
        if not raw_prompt:
            return ""

        key = RefinePrompt.bag_of_words(raw_prompt)
        cached = prompt_cache.cache.get(key)
        if cached:
            return cached

        # Lightweight refinement fallback for offline reliability.
        refined = (
            "Analyze the user goal, navigate efficiently, use tools when needed, "
            "and return a concise JSON final answer.\n"
            f"User request: {raw_prompt}"
        )
        prompt_cache.cache[key] = refined
        return refined
