"""L2 Tools Layer — task-relevant tool and skill RAG.

Analogous to L2 cache: fast, medium size, retrieved per task.
Indexes all registered tools + SKILLS.md entries, then retrieves
only the top-k most relevant to the current intent.

Token budget: ~800 tokens.
"""

from __future__ import annotations

from typing import List, Tuple

from smolclaw.cognitive.context.retrieval import rank, estimate_tokens, truncate_to_budget

TOKEN_BUDGET = 800


def _build_tool_corpus() -> List[Tuple[str, str]]:
    """Build (name, description) corpus from all registered tools."""
    corpus: List[Tuple[str, str]] = []
    try:
        from smolclaw.agent.tools.ToolRegistry import ToolRegistry
        for tool in ToolRegistry.get_all_tools():
            name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
            desc = getattr(tool, "description", "") or ""
            corpus.append((str(name), f"{name}: {desc}"))
    except Exception:
        pass
    return corpus


def _build_skills_corpus() -> List[Tuple[str, str]]:
    """Build (skill_name, skill_text) corpus from SKILLS.md."""
    corpus: List[Tuple[str, str]] = []
    try:
        from smolclaw.config import smolclaw_home_dir
        skills_path = smolclaw_home_dir() / "SKILLS.md"
        if not skills_path.exists():
            return corpus
        text = skills_path.read_text(encoding="utf-8")
        # Split on ## headings (each skill is a section)
        import re
        sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
        for section in sections[1:]:  # skip preamble
            lines = section.strip().splitlines()
            if lines:
                title = lines[0].strip()
                body = "\n".join(lines[1:]).strip()
                corpus.append((title, f"{title}: {body}"))
    except Exception:
        pass
    return corpus


class L2Tools:
    """Retrieves the most relevant tools and skills for a given task intent."""

    def __init__(self, top_k_tools: int = 8, top_k_skills: int = 3):
        self.top_k_tools = top_k_tools
        self.top_k_skills = top_k_skills
        self._tool_corpus: List[Tuple[str, str]] | None = None
        self._skills_corpus: List[Tuple[str, str]] | None = None

    def _tools(self) -> List[Tuple[str, str]]:
        if self._tool_corpus is None:
            self._tool_corpus = _build_tool_corpus()
        return self._tool_corpus

    def _skills(self) -> List[Tuple[str, str]]:
        if self._skills_corpus is None:
            self._skills_corpus = _build_skills_corpus()
        return self._skills_corpus

    def retrieve(self, intent: str) -> str:
        """Return relevant tools + skills block for this intent."""
        sections: List[str] = []
        budget_remaining = TOKEN_BUDGET

        # --- Tools ---
        tool_results = rank(intent, self._tools(), top_k=self.top_k_tools)
        if tool_results:
            lines = ["Available tools (most relevant to this task):"]
            for name, text, score in tool_results:
                if estimate_tokens("\n".join(lines)) >= budget_remaining * 0.7:
                    break
                lines.append(f"  • {text}")
            sections.append("\n".join(lines))

        # --- Skills ---
        skill_results = rank(intent, self._skills(), top_k=self.top_k_skills)
        if skill_results:
            lines = ["Relevant skills:"]
            for name, text, score in skill_results:
                if score < 0.05:
                    break
                lines.append(f"  • {text}")
            if len(lines) > 1:
                sections.append("\n".join(lines))

        block = "\n\n".join(sections)
        return truncate_to_budget(block, TOKEN_BUDGET)

    def invalidate(self) -> None:
        """Clear cached corpora (e.g. after new tools are registered)."""
        self._tool_corpus = None
        self._skills_corpus = None


__all__ = ["L2Tools"]
