"""Act interaction for smolhand contracts."""

from typing import List

from smolclaw.agent.entities.runtime.ExecutionContract import ExecutionContract
from smolclaw.agent.entities.runtime.ToolResult import ToolResult
from smolclaw.agent.interactions.smolhand.ExecuteCommand import ExecuteCommand


class SmolhandAct:
    @staticmethod
    def execute(contract: ExecutionContract, tool_map: dict) -> List[ToolResult]:
        outputs: List[ToolResult] = []
        for step in contract.steps:
            outputs.append(ExecuteCommand.execute(step.tool, step.arguments, tool_map))
        return outputs
