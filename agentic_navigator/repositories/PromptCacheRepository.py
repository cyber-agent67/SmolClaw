"""Prompt cache persistence repository."""

import json
import os
from typing import Dict


class PromptCacheRepository:
    @staticmethod
    def load(file_path: str) -> Dict[str, str]:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @staticmethod
    def save(file_path: str, cache: Dict[str, str]) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
