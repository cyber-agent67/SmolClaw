"""Explicit Deterministic Finite Automaton (DFA) for cognitive system runloop.

This module implements an explicit state machine with:
- Defined states (enum)
- Explicit transition table
- Transition guards
- Declarative state transitions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# =============================================================================
# Agent States (Explicit Enum)
# =============================================================================

class AgentState(Enum):
    """Explicit agent states for DFA."""
    AWAIT_INTENT = "await_intent"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAIT_CLARIFICATION = "await_clarification"
    DONE = "done"
    ERROR = "error"


# =============================================================================
# Events (Triggers for Transitions)
# =============================================================================

class AgentEvent(Enum):
    """Events that trigger state transitions."""
    INTENT_RECEIVED = "intent_received"
    PLAN_GENERATED = "plan_generated"generated
    PLAN_FAILED = "plan_failed"
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"
    CLARIFICATION_NEEDED = "clarification_needed"
    CLARIFICATION_RECEIVED = "clarification_received"
    GOAL_ACHIEVED = "goal_achieved"
    ERROR_OCCURRED = "error_occurred"
    TIMEOUT = "timeout"


# =============================================================================
# Transition Definition
# =============================================================================

@dataclass
class Transition:
    """Defines a state transition in the DFA.
    
    Attributes:
        from_state: Source state
        event: Event that triggers transition
        to_state: Destination state
        guard: Optional condition that must be true for transition
        action: Optional action to execute on transition
    """
    from_state: AgentState
    event: AgentEvent
    to_state: AgentState
    guard: Optional[Callable[[Dict[str, Any]], bool]] = None
    action: Optional[Callable[[Dict[str, Any]], Any]] = None
    
    def can_fire(self, context: Dict[str, Any]) -> bool:
        """Check if this transition can fire.
        
        Args:
            context: Current context/guard data
            
        Returns:
            True if transition can fire
        """
        if self.guard is None:
            return True
        return self.guard(context)
    
    def execute_action(self, context: Dict[str, Any]) -> Any:
        """Execute transition action if defined.
        
        Args:
            context: Current context
            
        Returns:
            Action result or None
        """
        if self.action is None:
            return None
        return self.action(context)


# =============================================================================
# Transition Table (Explicit DFA Definition)
# =============================================================================

class TransitionTable:
    """Explicit transition table for the cognitive system DFA.
    
    Defines all valid state transitions with guards and actions.
    """
    
    def __init__(self):
        """Initialize transition table with default transitions."""
        self.transitions: List[Transition] = []
        self._build_default_transitions()
    
    def _build_default_transitions(self) -> None:
        """Build default transition table."""
        
        # AWAIT_INTENT → PLANNING (on intent received)
        self.transitions.append(Transition(
            from_state=AgentState.AWAIT_INTENT,
            event=AgentEvent.INTENT_RECEIVED,
            to_state=AgentState.PLANNING,
            guard=lambda ctx: bool(ctx.get("intent")),
            action=lambda ctx: print(f"Processing intent: {ctx.get('intent')}"),
        ))
        
        # PLANNING → EXECUTING (on plan generated)
        self.transitions.append(Transition(
            from_state=AgentState.PLANNING,
            event=AgentEvent.PLAN_GENERATED,
            to_state=AgentState.EXECUTING,
            guard=lambda ctx: ctx.get("plan_confidence", 0) > 0.3,
            action=lambda ctx: print(f"Executing plan with confidence {ctx.get('plan_confidence')}"),
        ))
        
        # PLANNING → AWAIT_CLARIFICATION (plan needs clarification)
        self.transitions.append(Transition(
            from_state=AgentState.PLANNING,
            event=AgentEvent.CLARIFICATION_NEEDED,
            to_state=AgentState.AWAIT_CLARIFICATION,
            guard=lambda ctx: ctx.get("requires_clarification", False),
            action=lambda ctx: print("Clarification needed"),
        ))
        
        # PLANNING → ERROR (plan failed)
        self.transitions.append(Transition(
            from_state=AgentState.PLANNING,
            event=AgentEvent.PLAN_FAILED,
            to_state=AgentState.ERROR,
            action=lambda ctx: print(f"Plan failed: {ctx.get('error')}"),
        ))
        
        # EXECUTING → DONE (goal achieved)
        self.transitions.append(Transition(
            from_state=AgentState.EXECUTING,
            event=AgentEvent.GOAL_ACHIEVED,
            to_state=AgentState.DONE,
            guard=lambda ctx: ctx.get("success", False),
            action=lambda ctx: print(f"Goal achieved: {ctx.get('result')}"),
        ))
        
        # EXECUTING → EXECUTING (action executed, continue)
        self.transitions.append(Transition(
            from_state=AgentState.EXECUTING,
            event=AgentEvent.ACTION_EXECUTED,
            to_state=AgentState.EXECUTING,
            guard=lambda ctx: not ctx.get("goal_achieved", False),
            action=lambda ctx: print(f"Action executed: {ctx.get('action')}"),
        ))
        
        # EXECUTING → PLANNING (action failed, replan)
        self.transitions.append(Transition(
            from_state=AgentState.EXECUTING,
            event=AgentEvent.ACTION_FAILED,
            to_state=AgentState.PLANNING,
            guard=lambda ctx: ctx.get("can_retry", True),
            action=lambda ctx: print(f"Action failed, replanning: {ctx.get('error')}"),
        ))
        
        # EXECUTING → ERROR (action failed, can't retry)
        self.transitions.append(Transition(
            from_state=AgentState.EXECUTING,
            event=AgentEvent.ACTION_FAILED,
            to_state=AgentState.ERROR,
            guard=lambda ctx: not ctx.get("can_retry", True),
            action=lambda ctx: print(f"Action failed, no retry: {ctx.get('error')}"),
        ))
        
        # AWAIT_CLARIFICATION → PLANNING (clarification received)
        self.transitions.append(Transition(
            from_state=AgentState.AWAIT_CLARIFICATION,
            event=AgentEvent.CLARIFICATION_RECEIVED,
            to_state=AgentState.PLANNING,
            guard=lambda ctx: bool(ctx.get("clarification")),
            action=lambda ctx: print(f"Received clarification: {ctx.get('clarification')}"),
        ))
        
        # Any state → ERROR (on error)
        for state in AgentState:
            if state != AgentState.ERROR:
                self.transitions.append(Transition(
                    from_state=state,
                    event=AgentEvent.ERROR_OCCURRED,
                    to_state=AgentState.ERROR,
                    action=lambda ctx: print(f"Error occurred: {ctx.get('error')}"),
                ))
        
        # Any state → AWAIT_INTENT (on timeout in executing)
        for state in [AgentState.EXECUTING, AgentState.PLANNING]:
            self.transitions.append(Transition(
                from_state=state,
                event=AgentEvent.TIMEOUT,
                to_state=AgentState.AWAIT_INTENT,
                action=lambda ctx: print("Timeout, resetting"),
            ))
    
    def add_transition(self, transition: Transition) -> None:
        """Add a custom transition.
        
        Args:
            transition: Transition to add
        """
        self.transitions.append(transition)
    
    def find_transition(
        self,
        from_state: AgentState,
        event: AgentEvent,
        context: Dict[str, Any]
    ) -> Optional[Transition]:
        """Find a valid transition for state + event.
        
        Args:
            from_state: Current state
            event: Triggering event
            context: Guard context
            
        Returns:
            Matching transition or None
        """
        for transition in self.transitions:
            if transition.from_state == from_state and transition.event == event:
                if transition.can_fire(context):
                    return transition
        return None
    
    def get_all_transitions(self) -> List[Dict[str, str]]:
        """Get all transitions as dictionaries.
        
        Returns:
            List of transition descriptions
        """
        return [
            {
                "from": t.from_state.value,
                "event": t.event.value,
                "to": t.to_state.value,
                "has_guard": t.guard is not None,
                "has_action": t.action is not None,
            }
            for t in self.transitions
        ]


# =============================================================================
# DFA Engine (State Machine Executor)
# =============================================================================

@dataclass
class DFAState:
    """Current state of the DFA.
    
    Attributes:
        state: Current agent state
        context: Current context data
        history: List of (state, event) tuples
        version: State version (for event sourcing)
    """
    state: AgentState = AgentState.AWAIT_INTENT
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Tuple[AgentState, AgentEvent]] = field(default_factory=list)
    version: int = 0
    
    def transition_to(
        self,
        new_state: AgentState,
        event: AgentEvent
    ) -> "DFAState":
        """Create new state after transition (immutable).
        
        Args:
            new_state: New state
            event: Triggering event
            
        Returns:
            New DFAState
        """
        return DFAState(
            state=new_state,
            context=self.context.copy(),
            history=self.history + [(self.state, event)],
            version=self.version + 1,
        )
    
    def with_context(self, updates: Dict[str, Any]) -> DFAState:
        """Create new state with updated context (immutable).
        
        Args:
            updates: Context updates
            
        Returns:
            New DFAState
        """
        new_context = {**self.context, **updates}
        return DFAState(
            state=self.state,
            context=new_context,
            history=self.history,
            version=self.version,
        )


class DFAEngine:
    """Deterministic Finite Automaton engine.
    
    Executes state transitions based on events and guards.
    """
    
    def __init__(self, transition_table: TransitionTable = None):
        """Initialize DFA engine.
        
        Args:
            transition_table: Transition table to use
        """
        self.transition_table = transition_table or TransitionTable()
        self.current_state = DFAState()
    
    def reset(self) -> None:
        """Reset DFA to initial state."""
        self.current_state = DFAState()
    
    def fire_event(
        self,
        event: AgentEvent,
        context: Dict[str, Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """Fire an event and transition state.
        
        Args:
            event: Event to fire
            context: Optional context for guards
            
        Returns:
            (success, error_message)
        """
        # Merge context
        ctx = {**self.current_state.context, **(context or {})}
        
        # Find valid transition
        transition = self.transition_table.find_transition(
            self.current_state.state,
            event,
            ctx
        )
        
        if transition is None:
            return (False, f"No valid transition from {self.current_state.state} on {event}")
        
        # Execute action
        try:
            transition.execute_action(ctx)
        except Exception as e:
            return (False, f"Transition action failed: {e}")
        
        # Transition to new state
        self.current_state = self.current_state.transition_to(
            transition.to_state,
            event
        )
        self.current_state.context = ctx
        
        return (True, None)
    
    def get_state(self) -> AgentState:
        """Get current state.
        
        Returns:
            Current agent state
        """
        return self.current_state.state
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context.
        
        Returns:
            Current context dictionary
        """
        return self.current_state.context.copy()
    
    def get_history(self) -> List[Tuple[AgentState, AgentEvent]]:
        """Get transition history.
        
        Returns:
            List of (state, event) tuples
        """
        return self.current_state.history.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DFA state to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "state": self.current_state.state.value,
            "context": self.current_state.context,
            "version": self.current_state.version,
            "history_length": len(self.current_state.history),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_dfa() -> DFAEngine:
    """Create a new DFA engine.
    
    Returns:
        New DFAEngine instance
    """
    return DFAEngine()


def create_transition_table() -> TransitionTable:
    """Create a new transition table.
    
    Returns:
        New TransitionTable instance
    """
    return TransitionTable()


__all__ = [
    "AgentState",
    "AgentEvent",
    "Transition",
    "TransitionTable",
    "DFAState",
    "DFAEngine",
    "create_dfa",
    "create_transition_table",
]
