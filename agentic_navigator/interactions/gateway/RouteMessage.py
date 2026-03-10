"""Route gateway messages to runloop."""

from agentic_navigator.entities.runtime.Intent import Intent
from agentic_navigator.interactions.runloop.Execute import ExecuteRunloop


class RouteMessage:
    @staticmethod
    def execute(session_id: str, message: str) -> dict:
        intent = Intent()
        intent.session_id = session_id
        intent.user_input = message

        state = ExecuteRunloop.execute(intent)
        return {
            "session_id": session_id,
            "done": state.done,
            "final_answer": state.final_answer,
            "phase": state.current_phase,
        }
