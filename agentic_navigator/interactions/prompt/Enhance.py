"""Enhance prompt interaction."""


class EnhancePrompt:
    @staticmethod
    def execute(base_prompt: str, start_url: str) -> str:
        return (
            "You are SMOL claw. Navigate strategically and use tools precisely.\n"
            f"Start URL: {start_url}\n"
            "Return final result as JSON.\n\n"
            f"Task: {base_prompt}"
        )
