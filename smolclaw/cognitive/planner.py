"""Probabilistic planner for cognitive system.

This module implements a probabilistic planner that:
- Samples strategies from learned distributions
- Computes confidence from historical success rates
- Generates dynamic plans based on context
- Uses Bayesian updating for confidence learning
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from smolclaw.cognitive.effects import Effect, Result, Success, Error


# =============================================================================
# Strategy Definitions
# =============================================================================

@dataclass
class Strategy:
    """A planning strategy with learned probabilities."""
    name: str
    description: str
    prior_probability: float = 0.5  # Initial belief
    success_count: int = 0
    failure_count: int = 0
    
    @property
    def learned_probability(self) -> float:
        """Compute learned probability from success rate (Laplace smoothing)."""
        total = self.success_count + self.failure_count
        if total == 0:
            return self.prior_probability
        
        # Laplace smoothing to avoid zero probabilities
        return (self.success_count + 1) / (total + 2)
    
    @property
    def confidence(self) -> float:
        """Confidence based on sample size."""
        total = self.success_count + self.failure_count
        # Confidence increases with more samples
        return min(1.0, total / 10.0)  # Max confidence at 10 samples
    
    def update(self, success: bool) -> None:
        """Update strategy statistics with outcome."""
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "prior_probability": self.prior_probability,
            "learned_probability": self.learned_probability,
            "confidence": self.confidence,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


# =============================================================================
# Default Strategies
# =============================================================================

DEFAULT_STRATEGIES = [
    Strategy(
        name="direct_tool_use",
        description="Use tools directly to accomplish goal",
        prior_probability=0.6,
    ),
    Strategy(
        name="explore_then_act",
        description="Explore page first, then take action",
        prior_probability=0.3,
    ),
    Strategy(
        name="ask_clarification",
        description="Ask for clarification before proceeding",
        prior_probability=0.1,
    ),
]


# =============================================================================
# Probabilistic Planner
# =============================================================================

@dataclass
class Plan:
    """Planning result with probabilistic confidence."""
    goal: str = ""
    strategy: str = ""
    strategy_description: str = ""
    steps: List[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_tools: bool = False
    requires_navigation: bool = False
    done: bool = False
    final_answer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "goal": self.goal,
            "strategy": self.strategy,
            "strategy_description": self.strategy_description,
            "steps": self.steps,
            "confidence": self.confidence,
            "requires_tools": self.requires_tools,
            "requires_navigation": self.requires_navigation,
            "done": self.done,
            "final_answer": self.final_answer,
            "metadata": self.metadata,
        }


class ProbabilisticPlanner:
    """Probabilistic planner that learns from experience.
    
    Features:
    - Samples strategies from learned distributions
    - Computes confidence from historical data
    - Updates beliefs based on outcomes
    - Generates context-dependent plans
    """
    
    def __init__(self, strategies: List[Strategy] = None):
        """Initialize planner with strategies.
        
        Args:
            strategies: List of strategies to choose from
        """
        self.strategies = strategies or DEFAULT_STRATEGIES.copy()
        self.history: List[Tuple[str, bool]] = []  # (strategy_name, success)
    
    def sample_strategy(self, context: Dict[str, Any] = None) -> Strategy:
        """Sample a strategy based on learned probabilities.
        
        Uses roulette wheel selection (fitness proportionate selection).
        
        Args:
            context: Optional context for strategy selection
            
        Returns:
            Selected strategy
        """
        # Compute normalized probabilities
        probs = [s.learned_probability for s in self.strategies]
        total = sum(probs)
        
        if total == 0:
            # Fallback to uniform if all probabilities are zero
            return random.choice(self.strategies)
        
        # Normalize
        normalized = [p / total for p in probs]
        
        # Roulette wheel selection
        r = random.random()
        cumulative = 0.0
        
        for i, prob in enumerate(normalized):
            cumulative += prob
            if r <= cumulative:
                return self.strategies[i]
        
        # Fallback (shouldn't reach here)
        return self.strategies[-1]
    
    def compute_confidence(
        self,
        intent: str,
        strategy: Strategy,
        context: Dict[str, Any] = None
    ) -> float:
        """Compute confidence for a plan.
        
        Factors:
        - Strategy learned probability
        - Strategy confidence (sample size)
        - Intent clarity
        - Context match
        
        Args:
            intent: User intent string
            strategy: Selected strategy
            context: Optional context
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence from strategy
        base_confidence = strategy.learned_probability * strategy.confidence
        
        # Adjust for intent clarity (simple heuristic)
        intent_clarity = self._compute_intent_clarity(intent)
        
        # Adjust for context match (if context provided)
        context_match = 1.0
        if context:
            context_match = self._compute_context_match(strategy, context)
        
        # Combine factors
        confidence = base_confidence * intent_clarity * context_match
        
        return min(1.0, max(0.0, confidence))
    
    def generate_steps(
        self,
        strategy: Strategy,
        intent: str,
        context: Dict[str, Any] = None
    ) -> List[str]:
        """Generate plan steps based on strategy.
        
        Args:
            strategy: Selected strategy
            intent: User intent
            context: Optional context
            
        Returns:
            List of step descriptions
        """
        if strategy.name == "direct_tool_use":
            return [
                "Analyze goal and identify required tools",
                "Execute tool actions in sequence",
                "Verify results after each action",
                "Return final answer",
            ]
        elif strategy.name == "explore_then_act":
            return [
                "Observe current page state",
                "Explore available options",
                "Identify best path to goal",
                "Execute navigation/actions",
                "Return final answer",
            ]
        elif strategy.name == "ask_clarification":
            return [
                "Identify ambiguous aspects of goal",
                "Generate clarification questions",
                "Wait for user response",
                "Refine plan based on clarification",
                "Execute refined plan",
            ]
        else:
            # Default steps
            return [
                "Analyze goal",
                "Choose approach",
                "Execute actions",
                "Return result",
            ]
    
    def plan(
        self,
        intent: str,
        context: Dict[str, Any] = None
    ) -> Result[Plan, str]:
        """Generate a plan for the given intent.
        
        This is the main planning function that:
        1. Samples a strategy from learned distribution
        2. Computes confidence based on multiple factors
        3. Generates context-dependent steps
        
        Args:
            intent: User intent/goal
            context: Optional context information
            
        Returns:
            Result with Plan or error message
        """
        try:
            # Sample strategy
            strategy = self.sample_strategy(context)
            
            # Compute confidence
            confidence = self.compute_confidence(intent, strategy, context)
            
            # Generate steps
            steps = self.generate_steps(strategy, intent, context)
            
            # Create plan
            plan = Plan(
                goal=intent,
                strategy=strategy.name,
                strategy_description=strategy.description,
                steps=steps,
                confidence=confidence,
                requires_tools=strategy.name != "ask_clarification",
                requires_navigation=strategy.name == "explore_then_act",
                done=False,
                metadata={
                    "sampled_from": len(self.strategies),
                    "strategy_confidence": strategy.confidence,
                    "intent_clarity": self._compute_intent_clarity(intent),
                },
            )
            
            return Success(plan)
        
        except Exception as e:
            return Error(f"Planning failed: {e}")
    
    def update_from_outcome(
        self,
        strategy_name: str,
        success: bool
    ) -> None:
        """Update planner beliefs from outcome.
        
        Args:
            strategy_name: Name of strategy used
            success: Whether it succeeded
        """
        # Update strategy statistics
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                strategy.update(success)
                break
        
        # Record in history
        self.history.append((strategy_name, success))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get planner statistics."""
        return {
            "strategies": [s.to_dict() for s in self.strategies],
            "total_plans": len(self.history),
            "success_rate": (
                sum(1 for _, success in self.history if success) / len(self.history)
                if self.history else 0.0
            ),
        }
    
    # Private helpers
    
    def _compute_intent_clarity(self, intent: str) -> float:
        """Compute how clear the intent is (0.0 to 1.0)."""
        if not intent:
            return 0.0
        
        # Simple heuristics:
        # - Longer intents tend to be clearer
        # - Intents with specific keywords are clearer
        length_score = min(1.0, len(intent) / 50.0)  # Max at 50 chars
        
        # Check for specific/actionable keywords
        actionable_keywords = [
            "find", "get", "extract", "click", "navigate", "search",
            "list", "show", "tell", "what", "how", "where",
        ]
        has_actionable = any(kw in intent.lower() for kw in actionable_keywords)
        
        clarity = (length_score + (1.0 if has_actionable else 0.5)) / 2
        return min(1.0, max(0.0, clarity))
    
    def _compute_context_match(
        self,
        strategy: Strategy,
        context: Dict[str, Any]
    ) -> float:
        """Compute how well strategy matches context."""
        # Simple implementation - can be enhanced with ML
        if strategy.name == "explore_then_act":
            # This strategy works better when we have navigation options
            has_links = context.get("link_count", 0) > 0
            return 1.0 if has_links else 0.7
        elif strategy.name == "direct_tool_use":
            # Works well when tools are available
            has_tools = context.get("tools_available", True)
            return 1.0 if has_tools else 0.5
        else:
            return 1.0


# =============================================================================
# Effectful Planner (for integration with cognitive system)
# =============================================================================

def create_planner_effect(
    strategies: List[Strategy] = None
) -> Effect[ProbabilisticPlanner]:
    """Effect: Create a new probabilistic planner."""
    return Effect.pure(ProbabilisticPlanner(strategies))


def plan_effect(
    planner: ProbabilisticPlanner,
    intent: str,
    context: Dict[str, Any] = None
) -> Effect[Result[Plan, str]]:
    """Effect: Generate plan from intent."""
    return Effect.pure(planner.plan(intent, context))


def update_planner_effect(
    planner: ProbabilisticPlanner,
    strategy_name: str,
    success: bool
) -> Effect[ProbabilisticPlanner]:
    """Effect: Update planner with outcome."""
    def compute() -> ProbabilisticPlanner:
        planner.update_from_outcome(strategy_name, success)
        return planner
    
    return Effect(compute)


__all__ = [
    "Strategy",
    "Plan",
    "ProbabilisticPlanner",
    "DEFAULT_STRATEGIES",
    "create_planner_effect",
    "plan_effect",
    "update_planner_effect",
]
