"""Layered context system — dynamic token-efficient prompt assembly.

Mirrors CPU cache hierarchy:
  L1  Identity    ~200 tok  always-on persona (SOUL.md)
  L2  Tools       ~800 tok  task-relevant tool/skill RAG
  L3  Session     ~400 tok  hot session memory + smolQ state
  L4  Long-term   ~300 tok  cold past-experience retrieval
  ────────────────────────
  Total           ~1700 tok (vs 100K+ naive dump)

Usage:
    from smolclaw.cognitive.context import ContextBuilder

    builder = ContextBuilder()
    system_prompt = builder.build(intent, event_store=loop.event_store)
"""

from smolclaw.cognitive.context.builder import ContextBuilder
from smolclaw.cognitive.context.retrieval import rank, estimate_tokens, truncate_to_budget

__all__ = [
    "ContextBuilder",
    "rank",
    "estimate_tokens",
    "truncate_to_budget",
]
