"""Save result interaction."""

import json
import os


class SaveResult:
    @staticmethod
    def execute(output_path: str, result) -> None:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        payload = result if result else {"error": "No result returned"}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
