"""Resolve action interaction."""

from smolclaw.agent.entities.actions.DeclarativeAction import DeclarativeAction
from smolclaw.agent.entities.runtime.ExecutionContract import ExecutionContract


class ResolveAction:
    @staticmethod
    def execute(action: DeclarativeAction) -> ExecutionContract:
        contract = ExecutionContract()
        contract.declarative_intent = action.intent or action.raw_instruction
        return contract
