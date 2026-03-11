"""Generate planner output interaction."""

from smolclaw.agent.entities.runtime.Intent import Intent
from smolclaw.agent.entities.runtime.Plan import Plan


class GeneratePlan:
    @staticmethod
    def execute(intent: Intent) -> Plan:
        plan = Plan()
        plan.goal = intent.user_input
        plan.requires_tools = True
        plan.requires_navigation = True
        plan.strategy = "Observe page, use tools, iterate until goal is met."
        plan.steps_description = [
            "Observe page state",
            "Choose tool actions",
            "Execute actions",
            "Return final answer",
        ]
        plan.confidence = 0.5
        return plan
