"""Save prompt cache interaction."""

from smolclaw.agent.entities.memory.PromptCache import PromptCache
from smolclaw.agent.repositories.PromptCacheRepository import PromptCacheRepository


class SaveCache:
    @staticmethod
    def execute(prompt_cache: PromptCache) -> PromptCache:
        PromptCacheRepository.save(prompt_cache.cache_file, prompt_cache.cache)
        return prompt_cache
