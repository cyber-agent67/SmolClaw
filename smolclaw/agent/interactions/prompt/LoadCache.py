"""Load prompt cache interaction."""

from smolclaw.agent.entities.memory.PromptCache import PromptCache
from smolclaw.agent.repositories.PromptCacheRepository import PromptCacheRepository


class LoadCache:
    @staticmethod
    def execute(prompt_cache: PromptCache) -> PromptCache:
        prompt_cache.cache = PromptCacheRepository.load(prompt_cache.cache_file)
        return prompt_cache
