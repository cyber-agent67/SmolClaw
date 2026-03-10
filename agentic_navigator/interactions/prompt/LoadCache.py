"""Load prompt cache interaction."""

from agentic_navigator.entities.memory.PromptCache import PromptCache
from agentic_navigator.repositories.PromptCacheRepository import PromptCacheRepository


class LoadCache:
    @staticmethod
    def execute(prompt_cache: PromptCache) -> PromptCache:
        prompt_cache.cache = PromptCacheRepository.load(prompt_cache.cache_file)
        return prompt_cache
