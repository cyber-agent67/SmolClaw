"""Navigation stack persistence repository."""

import json
import os
from typing import List


class NavigationStackRepository:
    @staticmethod
    def save(file_path: str, stack: List[str]) -> None:
        """Persists the navigation stack to a file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stack, f, indent=2)

    @staticmethod
    def load(file_path: str) -> List[str]:
        """Loads a navigation stack from a file."""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
