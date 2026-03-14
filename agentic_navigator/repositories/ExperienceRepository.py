"""Experience persistence repository."""

import json
import os
from typing import List

from core.memory.store import Experience, from_dict, to_dict


class ExperienceRepository:
    @staticmethod
    def load(file_path: str) -> List[Experience]:
        """Loads experiences from a JSON file."""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                return [from_dict(item) for item in payload]
            except Exception:
                return []
        return []

    @staticmethod
    def save(file_path: str, experiences: List[Experience]) -> None:
        """Saves experiences to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([to_dict(exp) for exp in experiences], f, indent=2)
