"""L1 Identity Layer — always-on bot persona.

Analogous to L1 cache: tiny, always present, never evicted.
Reads from ~/.smolclaw/SOUL.md + hard-coded core constraints.

Token budget: ~200 tokens.
"""

from __future__ import annotations

from smolclaw.cognitive.context.retrieval import truncate_to_budget

TOKEN_BUDGET = 200

_DEFAULT_IDENTITY = """You are SmolClaw, an autonomous browser navigation agent.
Core principles:
- Complete tasks efficiently using available tools
- Learn from each navigation step via Q-learning
- Ask for clarification only when genuinely ambiguous
- Always prefer the simplest path to the goal"""


class L1Identity:
    """Loads and caches the bot identity/persona."""

    def __init__(self):
        self._cached: str | None = None

    def _load_soul(self) -> str:
        try:
            from smolclaw.config import smolclaw_home_dir
            soul_path = smolclaw_home_dir() / "SOUL.md"
            if soul_path.exists():
                content = soul_path.read_text(encoding="utf-8").strip()
                # Strip markdown headings, keep body
                lines = [l for l in content.splitlines() if not l.startswith("# SOUL")]
                return "\n".join(lines).strip()
        except Exception:
            pass
        return _DEFAULT_IDENTITY

    def get(self) -> str:
        """Return the L1 identity block, truncated to token budget."""
        if self._cached is None:
            self._cached = truncate_to_budget(self._load_soul(), TOKEN_BUDGET)
        return self._cached

    def invalidate(self) -> None:
        """Force reload on next get() (e.g. after SOUL.md edit)."""
        self._cached = None


__all__ = ["L1Identity"]
