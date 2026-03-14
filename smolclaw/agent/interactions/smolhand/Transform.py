"""Transform declarative instructions into imperative commands."""

from smolclaw.agent.entities.runtime.ExecutionContract import ExecutionContract


class SmolhandTransform:
    @staticmethod
    def execute(contract: ExecutionContract) -> ExecutionContract:
        contract.imperative_commands = [f"{step.tool}({step.arguments})" for step in contract.steps]
        return contract
