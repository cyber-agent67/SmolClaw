"""Extract contract interaction from smolhand text output."""

import json

from smolclaw.agent.entities.runtime.ExecutionContract import ExecutionContract, ExecutionStep


class SmolhandExtract:
    @staticmethod
    def execute(text: str) -> ExecutionContract:
        contract = ExecutionContract()
        contract.raw_plan = text

        try:
            payload = json.loads(text)
            tool_calls = payload.get("tool_calls", []) if isinstance(payload, dict) else []
            for idx, call in enumerate(tool_calls, start=1):
                step = ExecutionStep()
                step.order = idx
                step.tool = call.get("name", "")
                step.arguments = call.get("arguments", {})
                step.description = call.get("description", "")
                contract.steps.append(step)
        except Exception:
            pass

        return contract
