"""Save prompt cache interaction."""

from agentic_navigator.entities.memory.PromptCache import PromptCache
from agentic_navigator.repositories.PromptCacheRepository import PromptCacheRepository


class SaveCache:
    @staticmethod
    def execute(prompt_cache: PromptCache) -> PromptCache:
        PromptCacheRepository.save(prompt_cache.cache_file, prompt_cache.cache)
        return prompt_cache
