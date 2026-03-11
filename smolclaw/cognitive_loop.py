#!/usr/bin/env python3
"""Cognitive runloop for SmolClaw - distributed cognitive system.

This runloop uses:
- Explicit DFA for state management
- Probabilistic planner for decision making
- Event sourcing for history and learning
- Pure functional effects for side effects
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, Optional

from smolclaw.cognitive import (
    # Effects
    Effect,
    Success,
    Error,
    # Planner
    ProbabilisticPlanner,
    Plan,
    # State Machine
    create_dfa,
    AgentState,
    AgentEvent,
    # Event Sourcing
    EventStore,
    IntentReceivedEvent,
    PlanGeneratedEvent,
    ToolExecutedEvent,
    TaskCompletedEvent,
    ErrorEvent,
    StateTransitionEvent,
    CognitiveSystemStore,
)


class CognitiveLoop:
    """Cognitive system runloop.
    
    Implements a full cognitive cycle:
    1. Receive intent
    2. Plan (probabilistic)
    3. Execute (effects)
    4. Learn (update planner)
    5. Record events (event sourcing)
    """
    
    def __init__(
        self,
        persistence_path: Optional[str] = None,
        max_loops: int = 10,
    ):
        """Initialize cognitive loop.
        
        Args:
            persistence_path: Optional path for event persistence
            max_loops: Maximum execution loops per intent
        """
        # Initialize cognitive components
        self.planner = ProbabilisticPlanner()
        self.dfa = create_dfa()
        self.event_store = EventStore(persistence_path)
        self.cognitive_store = CognitiveSystemStore(self.event_store)
        
        self.max_loops = max_loops
        self.start_time: Optional[float] = None
    
    def process_intent(self, intent: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process an intent through the cognitive cycle.
        
        Args:
            intent: User intent/goal
            context: Optional context information
            
        Returns:
            Execution result dictionary
        """
        self.start_time = time.time()
        context = context or {}
        
        # =====================================================================
        # Phase 1: Receive Intent
        # =====================================================================
        self._record_intent(intent)
        success, error = self.dfa.fire_event(
            AgentEvent.INTENT_RECEIVED,
            {"intent": intent}
        )
        
        if not success:
            return self._error_result(f"Failed to transition on intent: {error}")
        
        # =====================================================================
        # Phase 2: Plan (Probabilistic)
        # =====================================================================
        plan_result = self.planner.plan(intent, context)
        
        if not plan_result.is_success:
            self._record_error(plan_result.error)
            self.dfa.fire_event(AgentEvent.PLAN_FAILED, {"error": plan_result.error})
            return self._error_result(plan_result.error)
        
        plan = plan_result.value
        
        # Record plan event
        self._record_plan(plan)
        
        # Transition to executing (or clarification)
        if plan.strategy == "ask_clarification":
            self.dfa.fire_event(AgentEvent.CLARIFICATION_NEEDED, {})
            return self._clarification_result(plan)
        
        self.dfa.fire_event(
            AgentEvent.PLAN_GENERATED,
            {"plan_confidence": plan.confidence}
        )
        
        # =====================================================================
        # Phase 3: Execute (Effectful)
        # =====================================================================
        execution_result = self._execute_plan(plan, context)
        
        # =====================================================================
        # Phase 4: Learn and Complete
        # =====================================================================
        success = execution_result.get("success", False)
        
        # Update planner (learning!)
        self.planner.update_from_outcome(plan.strategy, success)
        
        # Record completion
        duration = time.time() - self.start_time
        self._record_completion(execution_result.get("result", ""), success, duration)
        
        if success:
            self.dfa.fire_event(AgentEvent.GOAL_ACHIEVED, execution_result)
        else:
            self.dfa.fire_event(AgentEvent.ERROR_OCCURRED, execution_result)
        
        return execution_result
    
    def _record_intent(self, intent: str) -> None:
        """Record intent received event."""
        self.event_store.append(IntentReceivedEvent(
            intent=intent,
            session_id="session_cognitive",
            source="cli",
        ))
    
    def _record_plan(self, plan: Plan) -> None:
        """Record plan generated event."""
        self.event_store.append(PlanGeneratedEvent(
            plan=plan.to_dict(),
            strategy=plan.strategy,
            confidence=plan.confidence,
        ))
        
        # Also record state transition
        self.event_store.append(StateTransitionEvent(
            from_state="await_intent",
            to_state="planning",
            trigger_event="plan_generated
        ))
    
    def _record_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: str,
        success: bool,
    ) -> None:
        """Record tool execution event."""
        self.event_store.append(ToolExecutedEvent(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
        ))
    
    def _record_completion(
        self,
        result: str,
        success: bool,
        duration: float,
    ) -> None:
        """Record task completion event."""
        self.event_store.append(TaskCompletedEvent(
            result=result,
            success=success,
            duration_seconds=duration,
        ))
    
    def _record_error(self, error_message: str) -> None:
        """Record error event."""
        self.event_store.append(ErrorEvent(
            error_message=error_message,
            recoverable=True,
        ))
    
    def _execute_plan(self, plan: Plan, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan steps.
        
        This is where actual tool execution happens.
        For now, uses a simple simulation.
        """
        loop_count = 0
        
        while loop_count < self.max_loops:
            loop_count += 1
            
            # Simulate tool execution
            # In real implementation, this would call actual tools
            for step in plan.steps:
                # Record tool execution
                self._record_tool_execution(
                    tool_name=step,
                    arguments={"step": step},
                    result=f"Executed: {step}",
                    success=True,
                )
                
                # Transition event
                self.event_store.append(StateTransitionEvent(
                    from_state="executing",
                    to_state="executing",
                    trigger_event="action_executed",
                ))
            
            # For simulation, assume success
            return {
                "success": True,
                "result": f"Completed plan with strategy: {plan.strategy}",
                "loops": loop_count,
                "steps_executed": len(plan.steps),
                "final_answer": f"Task completed using {plan.strategy}",
            }
        
        # Timeout
        return {
            "success": False,
            "result": "Execution timeout",
            "loops": loop_count,
            "error": f"Exceeded max loops ({self.max_loops})",
        }
    
    def _error_result(self, error: str) -> Dict[str, Any]:
        """Create error result."""
        return {
            "success": False,
            "error": error,
            "state": self.dfa.get_state().value,
        }
    
    def _clarification_result(self, plan: Plan) -> Dict[str, Any]:
        """Create clarification result."""
        return {
            "success": False,
            "requires_clarification": True,
            "plan": plan.to_dict(),
            "state": self.dfa.get_state().value,
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get current cognitive system state.
        
        Returns:
            State dictionary
        """
        return {
            "agent_state": self.dfa.get_state().value,
            "event_count": len(self.event_store),
            "version": self.event_store.get_version(),
            "planner_stats": self.planner.get_statistics(),
            "read_model": self.cognitive_store.ask(None),  # Get current read model
        }
    
    def get_history(self) -> list:
        """Get event history.
        
        Returns:
            List of events
        """
        return [e.to_dict() for e in self.event_store.events]
    
    def replay(self, from_version: int = 0) -> list:
        """Replay events from version.
        
        Args:
            from_version: Starting version
            
        Returns:
            List of events
        """
        events = self.event_store.replay(from_version)
        return [e.to_dict() for e in events]


def main():
    """Main cognitive loop entry point."""
    parser = argparse.ArgumentParser(description="SmolClaw Cognitive Runloop")
    parser.add_argument("--prompt", type=str, help="Intent/prompt to process")
    parser.add_argument(
        "--persistence-path",
        type=str,
        default=None,
        help="Path for event persistence",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=10,
        help="Maximum execution loops",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="cognitive_output.json",
        help="Output file for results",
    )
    parser.add_argument(
        "--show-state",
        action="store_true",
        help="Show cognitive system state",
    )
    parser.add_argument(
        "--replay",
        action="store_true",
        help="Replay event history",
    )
    
    args = parser.parse_args()
    
    # Initialize cognitive loop
    loop = CognitiveLoop(
        persistence_path=args.persistence_path,
        max_loops=args.max_loops,
    )
    
    # Show state if requested
    if args.show_state:
        state = loop.get_state()
        print(json.dumps(state, indent=2))
        return
    
    # Replay if requested
    if args.replay:
        events = loop.replay()
        print(json.dumps(events, indent=2))
        return
    
    # Process intent
    if args.prompt:
        result = loop.process_intent(args.prompt)
        
        # Save output
        output = {
            "intent": args.prompt,
            "result": result,
            "final_state": loop.get_state(),
        }
        
        # Save to file
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        print(f"Result: {json.dumps(result, indent=2)}")
        print(f"Output saved to: {args.output}")
    else:
        # Interactive mode
        print("SmolClaw Cognitive System Ready")
        print("Type 'exit' to quit, 'state' to show state, 'replay' to replay events")
        print()
        
        while True:
            try:
                intent = input("cognitive> ").strip()
                
                if not intent:
                    continue
                
                if intent.lower() in {"exit", "quit"}:
                    print("Goodbye!")
                    break
                
                if intent.lower() == "state":
                    state = loop.get_state()
                    print(json.dumps(state, indent=2))
                    continue
                
                if intent.lower() == "replay":
                    events = loop.replay()
                    print(json.dumps(events, indent=2))
                    continue
                
                # Process intent
                result = loop.process_intent(intent)
                print(json.dumps(result, indent=2))
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
