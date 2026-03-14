"""ContextBuilder — assembles the layered system prompt per task.

The prompt is built dynamically using the 4-layer cache hierarchy:

    L1 Identity   (~200 tok)  always present — bot persona
    L2 Tools      (~800 tok)  RAG — only relevant tools for THIS task
    L3 Session    (~400 tok)  hot — what happened this session + smolQ state
    L4 Long-term  (~300 tok)  cold — past successful patterns (if relevant)
    ─────────────────────────
    Total budget  ~1700 tok   vs. 100K+ naive full dump

The system prompt is assembled fresh on each call to build(), so every
agent run gets exactly the context it needs and nothing else.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from smolclaw.cognitive.context.layers.l1_identity import L1Identity
from smolclaw.cognitive.context.layers.l2_tools import L2Tools
from smolclaw.cognitive.context.layers.l3_session import L3Session
from smolclaw.cognitive.context.layers.l4_longterm import L4LongTerm
from smolclaw.cognitive.context.retrieval import estimate_tokens

if TYPE_CHECKING:
    from smolclaw.cognitive.event_sourcing import EventStore

_DIVIDER = "\n" + "─" * 60 + "\n"


class ContextBuilder:
    """Builds a token-efficient, task-specific system prompt.

    Usage:
        builder = ContextBuilder()
        system_prompt = builder.build(intent, event_store=loop.event_store)
    """

    def __init__(self):
        self.l1 = L1Identity()
        self.l2 = L2Tools()
        self.l3 = L3Session()
        self.l4 = L4LongTerm()

    def build(
        self,
        intent: str,
        event_store: Optional["EventStore"] = None,
    ) -> str:
        """Assemble the layered system prompt for this intent.

        Args:
            intent: The current task/intent being executed
            event_store: Live event store for L3 session memory

        Returns:
            Assembled system prompt string
        """
        blocks = []

        # L1 — Identity (always)
        l1 = self.l1.get()
        if l1:
            blocks.append(("IDENTITY", l1))

        # L2 — Relevant tools (RAG, per task)
        l2 = self.l2.retrieve(intent)
        if l2:
            blocks.append(("TOOLS & SKILLS", l2))

        # L3 — Session memory (hot)
        l3 = self.l3.get(event_store)
        if l3:
            blocks.append(("SESSION MEMORY", l3))

        # L4 — Long-term memory (cold, only if relevant)
        l4 = self.l4.retrieve(intent)
        if l4:
            blocks.append(("PAST EXPERIENCE", l4))

        # Assemble
        parts = []
        for section, content in blocks:
            parts.append(f"[{section}]\n{content}")

        prompt = _DIVIDER.join(parts)

        total_tokens = estimate_tokens(prompt)
        header = f"# SmolClaw Context — {total_tokens} tokens across {len(blocks)} layers\n\n"

        return header + prompt

    def invalidate_identity(self) -> None:
        """Force L1 reload (after SOUL.md edited)."""
        self.l1.invalidate()

    def invalidate_tools(self) -> None:
        """Force L2 reload (after new tools registered)."""
        self.l2.invalidate()

    def token_breakdown(self, intent: str, event_store: Optional["EventStore"] = None) -> dict:
        """Return token count per layer for debugging/monitoring."""
        return {
            "l1_identity": estimate_tokens(self.l1.get()),
            "l2_tools": estimate_tokens(self.l2.retrieve(intent)),
            "l3_session": estimate_tokens(self.l3.get(event_store)),
            "l4_longterm": estimate_tokens(self.l4.retrieve(intent)),
        }


__all__ = ["ContextBuilder"]
