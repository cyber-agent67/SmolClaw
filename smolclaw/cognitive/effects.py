"""Effect types for pure functional programming in SmolClaw cognitive system.

This module provides effect types that make side effects explicit and composable,
enabling pure functional programming patterns throughout the cognitive system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, List, Optional, TypeVar

T = TypeVar('T')
E = TypeVar('E')


@dataclass
class Effect(Generic[T]):
    """Represents a deferred computation that may have side effects.
    
    Effects are lazy - they don't execute until run() is called.
    This makes side effects explicit and composable.
    
    Example:
        >>> def read_file(path: str) -> Effect[str]:
        ...     return Effect(lambda: open(path).read())
        >>> 
        >>> effect = read_file("data.txt")  # Doesn't read yet
        >>> result = effect.run()  # Now it reads
    """
    compute: Callable[[], T]
    
    def run(self) -> T:
        """Execute the effect and return the result."""
        return self.compute()
    
    def map(self, f: Callable[[T], Any]) -> Effect[Any]:
        """Transform the result of this effect.
        
        Args:
            f: Function to apply to the result
            
        Returns:
            New effect that applies f when run
        """
        return Effect(lambda: f(self.run()))
    
    def flat_map(self, f: Callable[[T], Effect[Any]]) -> Effect[Any]:
        """Chain effects together (monadic bind).
        
        Args:
            f: Function that returns an effect
            
        Returns:
            Flattened effect chain
        """
        return f(self.run())
    
    @staticmethod
    def pure(value: T) -> Effect[T]:
        """Create an effect that just returns a value (no side effects).
        
        Args:
            value: Value to wrap
            
        Returns:
            Pure effect
        """
        return Effect(lambda: value)


@dataclass
class Result(Generic[T, E]):
    """Result type for error handling in pure functions.
    
    Either Success(value) or Error(error).
    Makes error handling explicit and type-safe.
    
    Example:
        >>> def safe_divide(a: float, b: float) -> Result[float, str]:
        ...     if b == 0:
        ...         return Error("Division by zero")
        ...     return Success(a / b)
    """
    value: Optional[T] = None
    error: Optional[E] = None
    is_success: bool = True
    
    @classmethod
    def success(cls, value: T) -> Result[T, E]:
        """Create a successful result."""
        return cls(value=value, is_success=True)
    
    @classmethod
    def failure(cls, error: E) -> Result[T, E]:
        """Create a failed result."""
        return cls(error=error, is_success=False)
    
    def map(self, f: Callable[[T], Any]) -> Result[Any, E]:
        """Transform success value."""
        if self.is_success:
            return Result.success(f(self.value))
        return Result.failure(self.error)
    
    def flat_map(self, f: Callable[[T], Result[Any, E]]) -> Result[Any, E]:
        """Chain result-producing functions."""
        if self.is_success:
            return f(self.value)
        return Result.failure(self.error)
    
    def get_or_else(self, default: T) -> T:
        """Get value or default if error."""
        return self.value if self.is_success else default


@dataclass
class State(Generic[T]):
    """State monad for threading state through pure computations.
    
    Represents a computation that produces a value and new state.
    
    Example:
        >>> def increment(state: dict) -> tuple[int, dict]:
        ...     new_state = {**state, 'count': state['count'] + 1}
        ...     return (new_state['count'], new_state)
        >>> 
        >>> state_effect = State(increment)
        >>> value, new_state = state_effect.run({'count': 0})
    """
    compute: Callable[[T], tuple[Any, T]]
    
    def run(self, state: T) -> tuple[Any, T]:
        """Execute with initial state, return (value, new_state)."""
        return self.compute(state)
    
    def map(self, f: Callable[[Any], Any]) -> State[T]:
        """Transform the result value."""
        return State(lambda s: (f(self.run(s)[0]), self.run(s)[1]))
    
    def flat_map(self, f: Callable[[Any], State[T]]) -> State[T]:
        """Chain stateful computations."""
        def chained(state: T) -> tuple[Any, T]:
            value, new_state = self.run(state)
            return f(value).run(new_state)
        return State(chained)


@dataclass
class Event:
    """Base class for all events in the cognitive system.
    
    Events are immutable records of what happened.
    All state changes are derived from event streams.
    """
    event_id: str = field(default_factory=lambda: "")
    event_type: str = field(default_factory=lambda: "event")
    timestamp: float = field(default_factory=lambda: 0.0)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class EventStream:
    """Immutable stream of events for event sourcing.
    
    Events can be appended but not modified (immutable).
    Supports replay and fold operations.
    """
    events: List[Event] = field(default_factory=list)
    
    def append(self, event: Event) -> EventStream:
        """Add event to stream (returns new stream, immutable)."""
        return EventStream(events=self.events + [event])
    
    def fold(self, initial: Any, reducer: Callable[[Any, Event], Any]) -> Any:
        """Reduce event stream to single value.
        
        Args:
            initial: Initial accumulator value
            reducer: Function (acc, event) -> new_acc
            
        Returns:
            Final accumulated value
        """
        acc = initial
        for event in self.events:
            acc = reducer(acc, event)
        return acc
    
    def filter_by_type(self, event_type: str) -> EventStream:
        """Filter events by type."""
        return EventStream(
            events=[e for e in self.events if e.event_type == event_type]
        )
    
    def from_version(self, version: int) -> EventStream:
        """Get events from a specific version onwards."""
        return EventStream(events=self.events[version:])
    
    def __len__(self) -> int:
        return len(self.events)
    
    def __iter__(self):
        return iter(self.events)


# Convenience constructors
def Success(value: T) -> Result[T, Any]:
    """Create successful result."""
    return Result.success(value)


def Error(error: E) -> Result[Any, E]:
    """Create failed result."""
    return Result.failure(error)


def pure(value: T) -> Effect[T]:
    """Create pure effect."""
    return Effect.pure(value)


def effect(compute: Callable[[], T]) -> Effect[T]:
    """Create effect from computation."""
    return Effect(compute)


__all__ = [
    "Effect",
    "Result",
    "State",
    "Event",
    "EventStream",
    "Success",
    "Error",
    "pure",
    "effect",
]
