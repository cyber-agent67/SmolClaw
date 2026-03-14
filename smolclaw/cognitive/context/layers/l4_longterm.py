"""L4 Long-term Memory Layer — cold archival retrieval.

Analogous to RAM/disk: slowest, largest, only fetched on a cache miss.
Retrieves past successful navigation experiences similar to the current
task, so the agent can reuse proven patterns.

Token budget: ~300 tokens. Only included when similarity > threshold.
"""

from __future__ import annotations

from typing import List, Tuple

from smolclaw.cognitive.context.retrieval import rank, estimate_tokens, truncate_to_budget

TOKEN_BUDGET = 300
SIMILARITY_THRESHOLD = 0.15  # Don't include irrelevant memories


def _load_experiences() -> List[Tuple[str, str]]:
    """Load all past experiences as (task, summary) pairs."""
    corpus: List[Tuple[str, str]] = []
    try:
        from smolclaw.agent.entities.memory.ExperienceMemory import ExperienceMemory
        from smolclaw.agent.interactions.memory.LoadExperiences import LoadExperiences

        mem = ExperienceMemory()
        LoadExperiences.execute(mem)

        for exp in mem.experiences:
            if not exp.success:
                continue  # Only include successful patterns
            summary = (
                f"Task: {exp.task[:100]} | "
                f"URL: {exp.start_url} → {exp.final_url} | "
                f"Result: {exp.result[:100]}"
            )
            corpus.append((exp.task, summary))
    except Exception:
        pass
    return corpus


class L4LongTerm:
    """Retrieves relevant past experiences for the current intent."""

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def retrieve(self, intent: str) -> str:
        """Return a relevant past-experience block, or empty string if no good match."""
        corpus = _load_experiences()
        if not corpus:
            return ""

        results = rank(intent, corpus, top_k=self.top_k)
        # Filter out low-relevance memories
        results = [(k, t, s) for k, t, s in results if s >= SIMILARITY_THRESHOLD]
        if not results:
            return ""

        lines = ["Relevant past experience (successful patterns):"]
        for _, summary, score in results:
            if estimate_tokens("\n".join(lines)) >= TOKEN_BUDGET:
                break
            lines.append(f"  • (relevance {score:.2f}) {summary}")

        block = "\n".join(lines)
        return truncate_to_budget(block, TOKEN_BUDGET)


__all__ = ["L4LongTerm"]
