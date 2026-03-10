"""AgentState entity - runloop state machine."""

from typing import Any, Dict, List, Optional


class AgentState:
    def __init__(self):
        self.goal: str = ""
        self.current_phase: str = "await_intent"
        self.context: List[str] = []
        self.tool_results: List[Dict[str, Any]] = []
        self.loop_count: int = 0
        self.max_loops: int = 10
        self.done: bool = False
        self.final_answer: Optional[str] = None
        self.error: Optional[str] = None
        self.current_url: str = ""
        self.page_description: str = ""
