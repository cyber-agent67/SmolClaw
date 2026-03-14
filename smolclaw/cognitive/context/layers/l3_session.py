"""L3 Session Layer — hot session memory.

Analogous to L3 cache: medium speed, scoped to the current session.
Summarises recent events from the EventStore and the smolQ navigation
state so the agent knows what it has already tried this session.

Token budget: ~400 tokens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from smolclaw.cognitive.context.retrieval import estimate_tokens, truncate_to_budget

if TYPE_CHECKING:
    from smolclaw.cognitive.event_sourcing import EventStore

TOKEN_BUDGET = 400


class L3Session:
    """Builds a compact session-memory block from live EventStore + smolQ."""

    def __init__(self, max_recent_events: int = 10):
        self.max_recent_events = max_recent_events

    def get(self, event_store: "EventStore | None" = None) -> str:
        sections: List[str] = []

        # --- Recent events ---
        if event_store is not None:
            events = list(event_store.events)[-self.max_recent_events:]
            if events:
                lines = ["Session history (most recent actions):"]
                for ev in events:
                    try:
                        d = ev.to_dict()
                        etype = d.get("event_type", "event")
                        # Pick the most informative field per event type
                        detail = (
                            d.get("tool_name")
                            or d.get("strategy")
                            or d.get("intent", "")[:80]
                            or d.get("result", "")[:80]
                            or d.get("error_message", "")[:80]
                        )
                        lines.append(f"  [{etype}] {detail}")
                    except Exception:
                        continue
                sections.append("\n".join(lines))

        # --- smolQ state ---
        try:
            from smolclaw.cognitive.smolQ.tool import get_q_state
            state = get_q_state()
            q_vals = state.get("q_values", {})
            task = state.get("current_task", "")
            if q_vals:
                # Show top-3 highest-scored pages
                top = sorted(q_vals.items(), key=lambda x: x[1], reverse=True)[:3]
                lines = [f"Q-learning state (task: {task[:60]}):"]
                for url, qv in top:
                    visits = state.get("visit_counts", {}).get(url, 0)
                    lines.append(f"  Q={qv:.3f} visits={visits}  {url[:80]}")
                sections.append("\n".join(lines))
        except Exception:
            pass

        if not sections:
            return ""

        block = "\n\n".join(sections)
        return truncate_to_budget(block, TOKEN_BUDGET)


__all__ = ["L3Session"]
