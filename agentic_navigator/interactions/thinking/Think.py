"""Think interaction - Claude-powered cognitive engine."""

import os

from smolclaw.templates_loader import render_template


class Think:
    @staticmethod
    def execute(query: str) -> str:
        """Pauses to reason strategically before acting."""
        try:
            import anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                return "Thinking Error: ANTHROPIC_API_KEY not found in environment."

            client = anthropic.Anthropic(api_key=api_key)

            thought_tool = {
                "name": "thought_engine",
                "description": "A tool for extended cognition.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reasoning": {"type": "string", "description": "Step-by-step planning."},
                        "confidence_score": {"type": "number", "description": "0-1 confidence."},
                    },
                    "required": ["reasoning"],
                },
            }

            system_prompt = render_template("prompts/think_system.md")
            messages = [{"role": "user", "content": query}]

            response = client.beta.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4000,
                system=system_prompt,
                tools=[thought_tool],
                tool_choice={"type": "tool", "name": "thought_engine"},
                messages=messages,
                betas=["context-1m-2025-08-07"],
            )

            thought_output = "No reasoning provided."
            tool_use_id = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "thought_engine":
                    thought_output = block.input.get("reasoning", "")
                    tool_use_id = block.id
                    break

            messages.append({"role": "assistant", "content": response.content})

            if tool_use_id:
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": "Thoughts recorded successfully.",
                            }
                        ],
                    }
                )

            messages.append(
                {
                    "role": "user",
                    "content": "Thought processed. Now execute your plan and provide the final response.",
                }
            )

            final_response = client.beta.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4000,
                system=render_template("prompts/think_finalize_system.md"),
                messages=messages,
                betas=["context-1m-2025-08-07"],
            )

            return (
                f"--- THOUGHT ENGINE ---\n{thought_output}\n\n"
                f"--- STRATEGIC PLAN ---\n{final_response.content[0].text}"
            )

        except Exception as e:
            return f"Thinking unavailable: {str(e)}"
