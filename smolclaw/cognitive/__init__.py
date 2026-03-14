"""Cognitive system core for SmolClaw.

This package provides the cognitive system architecture:
- Effect types for pure functional programming
- Event sourcing for state management
- Probabilistic planning
- Explicit state machines (DFA)
"""

from smolclaw.cognitive.effects import (
    Effect,
    Result,
    State,
    Event,
    EventStream,
    Success,
    Error,
    pure,
    effect,
)

from smolclaw.cognitive.planner import (
    Strategy,
    Plan,
    ProbabilisticPlanner,
    DEFAULT_STRATEGIES,
)

from smolclaw.cognitive.state_machine import (
    AgentState,
    AgentEvent,
    Transition,
    TransitionTable,
    DFAState,
    DFAEngine,
    create_dfa,
)

from smolclaw.cognitive.event_sourcing import (
    IntentReceivedEvent,
    PlanGeneratedEvent,
    ToolExecutedEvent,
    NavigationEvent,
    StateTransitionEvent,
    TaskCompletedEvent,
    ErrorEvent,
    EventStore,
    Command,
    Query,
    CognitiveSystemStore,
)

from smolclaw.cognitive.context import ContextBuilder

from smolclaw.cognitive.smolQ import (
    QLearningScoreEntity,
    QLearningState,
    ScoreTaskProgress,
    score_task_progress_q_learning,
    get_q_state,
    reset_q_state,
)

__all__ = [
    # Context
    "ContextBuilder",
    # Effects
    "Effect",
    "Result",
    "State",
    "Event",
    "EventStream",
    "Success",
    "Error",
    "pure",
    "effect",
    # Planner
    "Strategy",
    "Plan",
    "ProbabilisticPlanner",
    "DEFAULT_STRATEGIES",
    # State Machine
    "AgentState",
    "AgentEvent",
    "Transition",
    "TransitionTable",
    "DFAState",
    "DFAEngine",
    "create_dfa",
    # Event Sourcing
    "IntentReceivedEvent",
    "PlanGeneratedEvent",
    "ToolExecutedEvent",
    "NavigationEvent",
    "StateTransitionEvent",
    "TaskCompletedEvent",
    "ErrorEvent",
    "EventStore",
    "Command",
    "Query",
    "CognitiveSystemStore",
    # smolQ
    "QLearningScoreEntity",
    "QLearningState",
    "ScoreTaskProgress",
    "score_task_progress_q_learning",
    "get_q_state",
    "reset_q_state",
]
