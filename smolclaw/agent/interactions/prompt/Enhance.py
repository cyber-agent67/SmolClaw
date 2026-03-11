"""Enhance prompt interaction."""

from smolclaw.templates_loader import render_template


class EnhancePrompt:
    @staticmethod
    def execute(base_prompt: str, start_url: str) -> str:
        return render_template(
            "prompts/enhance_prompt.md",
            {
                "start_url": start_url,
                "base_prompt": base_prompt,
            },
        )
