#!/usr/bin/env python3
"""Cognitive runloop for SmolClaw.

Architecture:
  1. Receive intent
  2. Build layered context (L1 identity → L2 tools RAG → L3 session → L4 long-term)
  3. Plan (probabilistic strategy selection)
  4. Execute (real agent via agentic_runner, driven by cognitive context)
  5. Learn (update planner + smolQ)
  6. Record (event sourcing)
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, Optional

from smolclaw.cognitive import (
    Effect,
    Success,
    Error,
    ProbabilisticPlanner,
    Plan,
    create_dfa,
    AgentState,
    AgentEvent,
    EventStore,
    IntentReceivedEvent,
    PlanGeneratedEvent,
    ToolExecutedEvent,
    TaskCompletedEvent,
    ErrorEvent,
    StateTransitionEvent,
    CognitiveSystemStore,
)
from smolclaw.cognitive.context import ContextBuilder


class CognitiveLoop:
    """Cognitive system runloop — intent → context → plan → agent → learn.

    The CognitiveLoop is the single entry point for all agent execution.
    It connects:
      - ContextBuilder: builds a token-efficient system prompt per task
      - ProbabilisticPlanner: selects execution strategy
      - agentic_runner: runs the real smolagents browser agent
      - EventStore: records everything for replay and learning
      - smolQ: updates Q-values from navigation outcomes
    """

    def __init__(
        self,
        persistence_path: Optional[str] = None,
        max_loops: int = 10,
        start_url: str = "https://www.google.com",
    ):
        self.planner = ProbabilisticPlanner()
        self.dfa = create_dfa()
        self.event_store = EventStore(persistence_path)
        self.cognitive_store = CognitiveSystemStore(self.event_store)
        self.context_builder = ContextBuilder()
        self.max_loops = max_loops
        self.start_url = start_url
        self.start_time: Optional[float] = None

    def process_intent(
        self,
        intent: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process an intent through the full cognitive cycle.

        Args:
            intent: User intent / task description
            context: Optional extra context (url override, session id, etc.)

        Returns:
            Execution result dict with success, result, loops, events
        """
        self.start_time = time.time()
        context = context or {}

        # ── Phase 1: Receive Intent ──────────────────────────────────────────
        self._record_intent(intent)
        ok, err = self.dfa.fire_event(AgentEvent.INTENT_RECEIVED, {"intent": intent})
        if not ok:
            return self._error_result(f"State machine rejected intent: {err}")

        # ── Phase 2: Build Layered Context ───────────────────────────────────
        system_prompt = self.context_builder.build(intent, event_store=self.event_store)

        # ── Phase 3: Plan ────────────────────────────────────────────────────
        plan_result = self.planner.plan(intent, context)
        if not plan_result.is_success:
            self._record_error(plan_result.error)
            self.dfa.fire_event(AgentEvent.PLAN_FAILED, {"error": plan_result.error})
            return self._error_result(plan_result.error)

        plan = plan_result.value
        self._record_plan(plan)

        if plan.strategy == "ask_clarification":
            self.dfa.fire_event(AgentEvent.CLARIFICATION_NEEDED, {})
            return self._clarification_result(plan)

        self.dfa.fire_event(AgentEvent.PLAN_GENERATED, {"plan_confidence": plan.confidence})

        # ── Phase 4: Execute ─────────────────────────────────────────────────
        start_url = context.get("url", self.start_url)
        execution_result = self._execute_with_agent(intent, system_prompt, start_url, plan)

        # ── Phase 5: Learn ───────────────────────────────────────────────────
        success = execution_result.get("success", False)
        self.planner.update_from_outcome(plan.strategy, success)

        duration = time.time() - self.start_time
        self._record_completion(execution_result.get("result", ""), success, duration)

        if success:
            self.dfa.fire_event(AgentEvent.GOAL_ACHIEVED, execution_result)
        else:
            self.dfa.fire_event(AgentEvent.ERROR_OCCURRED, execution_result)

        execution_result["context_tokens"] = self.context_builder.token_breakdown(
            intent, self.event_store
        )
        return execution_result

    # ── Agent execution ───────────────────────────────────────────────────────

    def _execute_with_agent(
        self,
        intent: str,
        system_prompt: str,
        start_url: str,
        plan: Plan,
    ) -> Dict[str, Any]:
        """Run the real browser agent, driven by the cognitive context prompt."""
        try:
            import argparse as _ap
            from smolclaw.agentic_runner import run_agent_with_args, cleanup_resources

            # Build args namespace the agent runner expects
            args = _ap.Namespace(
                url=start_url,
                prompt=f"{system_prompt}\n\n---\n\nTask: {intent}",
                output=os.path.join("data", "cognitive_output.json"),
                model_type="LiteLLMModel",
                model_id=os.environ.get("SMOLCLAW_MODEL", "gpt-4o"),
                iterations=1,
                continue_on_error=False,
                await_commands=False,
                command_source="stdin",
                command_queue_file="",
            )

            try:
                result = run_agent_with_args(args)
                self._record_tool_execution(
                    tool_name="agentic_runner",
                    arguments={"intent": intent, "url": start_url},
                    result=str(result)[:500] if result else "no result",
                    success=bool(result),
                )
                return {
                    "success": bool(result),
                    "result": str(result) if result else "Agent returned no result",
                    "strategy": plan.strategy,
                    "confidence": plan.confidence,
                }
            finally:
                try:
                    cleanup_resources()
                except Exception:
                    pass

        except ImportError:
            # Agentic runner not available — fall back to smolhand
            return self._execute_with_smolhand(intent, system_prompt, plan)
        except Exception as exc:
            self._record_error(str(exc))
            return {
                "success": False,
                "error": str(exc),
                "strategy": plan.strategy,
                "result": f"Execution failed: {exc}",
            }

    def _execute_with_smolhand(
        self,
        intent: str,
        system_prompt: str,
        plan: Plan,
    ) -> Dict[str, Any]:
        """Fallback: run via smolhand tool-calling runtime."""
        try:
            from smolclaw.tools.smolhand import SmolhandRunner, OpenAICompatClient
            from smolclaw.config import load_config

            cfg = load_config()
            llm = OpenAICompatClient(
                model=cfg.get("model", "gpt-4o"),
                base_url=cfg.get("base_url", "https://api.openai.com/v1"),
                api_key=cfg.get("api_key", os.environ.get("OPENAI_API_KEY", "")),
            )
            runner = SmolhandRunner(llm_client=llm)
            result = runner.run(
                f"{system_prompt}\n\n---\n\nTask: {intent}",
                max_loops=self.max_loops,
            )
            self._record_tool_execution("smolhand_runner", {"intent": intent}, str(result)[:500], True)
            return {"success": True, "result": str(result), "strategy": plan.strategy}
        except Exception as exc:
            return {"success": False, "error": str(exc), "result": f"Smolhand failed: {exc}"}

    # ── Event recording ───────────────────────────────────────────────────────

    def _record_intent(self, intent: str) -> None:
        self.event_store.append(IntentReceivedEvent(
            intent=intent, session_id="session_cognitive", source="cli",
        ))

    def _record_plan(self, plan: Plan) -> None:
        self.event_store.append(PlanGeneratedEvent(
            plan=plan.to_dict(), strategy=plan.strategy, confidence=plan.confidence,
        ))
        self.event_store.append(StateTransitionEvent(
            from_state="await_intent", to_state="planning", trigger_event="plan_generated",
        ))

    def _record_tool_execution(
        self, tool_name: str, arguments: Dict[str, Any], result: str, success: bool,
    ) -> None:
        self.event_store.append(ToolExecutedEvent(
            tool_name=tool_name, arguments=arguments, result=result, success=success,
        ))

    def _record_completion(self, result: str, success: bool, duration: float) -> None:
        self.event_store.append(TaskCompletedEvent(
            result=result, success=success, duration_seconds=duration,
        ))

    def _record_error(self, error_message: str) -> None:
        self.event_store.append(ErrorEvent(error_message=error_message, recoverable=True))

    # ── State / replay ────────────────────────────────────────────────────────

    def _error_result(self, error: str) -> Dict[str, Any]:
        return {"success": False, "error": error, "state": self.dfa.get_state().value}

    def _clarification_result(self, plan: Plan) -> Dict[str, Any]:
        return {
            "success": False,
            "requires_clarification": True,
            "plan": plan.to_dict(),
            "state": self.dfa.get_state().value,
        }

    def get_state(self) -> Dict[str, Any]:
        return {
            "agent_state": self.dfa.get_state().value,
            "event_count": len(self.event_store),
            "version": self.event_store.get_version(),
            "planner_stats": self.planner.get_statistics(),
            "read_model": self.cognitive_store.ask(None),
        }

    def get_history(self) -> list:
        return [e.to_dict() for e in self.event_store.events]

    def replay(self, from_version: int = 0) -> list:
        return [e.to_dict() for e in self.event_store.replay(from_version)]


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SmolClaw Cognitive Runloop")
    parser.add_argument("--prompt", type=str, help="Intent/prompt to process")
    parser.add_argument("--url", type=str, default="https://www.google.com", help="Start URL")
    parser.add_argument("--persistence-path", type=str, default=None)
    parser.add_argument("--max-loops", type=int, default=10)
    parser.add_argument("--output", type=str, default="cognitive_output.json")
    parser.add_argument("--show-state", action="store_true")
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--show-context", action="store_true", help="Print layered context for prompt")
    args = parser.parse_args()

    loop = CognitiveLoop(
        persistence_path=args.persistence_path,
        max_loops=args.max_loops,
        start_url=args.url,
    )

    if args.show_state:
        print(json.dumps(loop.get_state(), indent=2))
        return

    if args.replay:
        print(json.dumps(loop.replay(), indent=2))
        return

    if args.show_context and args.prompt:
        ctx = loop.context_builder.build(args.prompt, loop.event_store)
        breakdown = loop.context_builder.token_breakdown(args.prompt, loop.event_store)
        print("─" * 60)
        print(ctx)
        print("─" * 60)
        print("Token breakdown:", json.dumps(breakdown, indent=2))
        return

    if args.prompt:
        result = loop.process_intent(args.prompt, context={"url": args.url})
        output = {"intent": args.prompt, "result": result, "final_state": loop.get_state()}

        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(json.dumps(result, indent=2))
        print(f"\nOutput saved to: {args.output}")
    else:
        print("SmolClaw Cognitive System Ready")
        print("Commands: 'exit', 'state', 'replay', 'context <intent>'")
        while True:
            try:
                intent = input("cognitive> ").strip()
                if not intent:
                    continue
                if intent.lower() in {"exit", "quit"}:
                    break
                if intent.lower() == "state":
                    print(json.dumps(loop.get_state(), indent=2))
                    continue
                if intent.lower() == "replay":
                    print(json.dumps(loop.replay(), indent=2))
                    continue
                if intent.lower().startswith("context "):
                    q = intent[8:].strip()
                    print(loop.context_builder.build(q, loop.event_store))
                    continue
                result = loop.process_intent(intent)
                print(json.dumps(result, indent=2))
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
