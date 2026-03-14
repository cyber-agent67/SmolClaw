"""PromptCache entity - pure state container."""

from typing import Dict


class PromptCache:
    def __init__(self):
        self.cache_file: str = "keyword_cache.json"
        self.cache: Dict[str, str] = {}
