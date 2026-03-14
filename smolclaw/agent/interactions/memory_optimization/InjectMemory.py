#!/usr/bin/env python3
"""InjectMemory interaction — THE TOKEN SAVER.

This is the main interaction for token-optimized memory injection.
Call this before every LLM request to inject surgically precise
context within budget.

Flow (Phase 1 - Recent):
1. Budget → Calculate available tokens
2. Select → Take recent experiences
3. Compress → Compress each experience 5x
4. Format → Format for prompt injection
5. Return → String ready for LLM prompt

Flow (Phase 2 - Semantic):
1. Budget → Calculate available tokens
2. Embed → Embed query and memories (local, free)
3. Search → Find semantically relevant memories
4. Compress → Already compressed
5. Format → Format for prompt injection
6. Return → String ready for LLM prompt

Result: 100K tokens → 2K tokens (98% reduction)
"""

from typing import List, Optional
from smolclaw.agent.entities.memory.Experience import Experience
from smolclaw.agent.entities.TokenBudget import TokenBudget
from smolclaw.agent.entities.CompressedMemory import CompressedMemory
from smolclaw.agent.entities.MemoryQuery import MemoryQuery
from smolclaw.agent.config.MemoryConfig import MemoryConfig
from smolclaw.agent.interactions.memory_optimization.CompressExperience import (
    CompressExperience
)
from smolclaw.agent.interactions.memory_optimization.SemanticSearch import (
    SemanticSearch
)


class InjectMemory:
    """Token-optimized memory injection.
    
    THE PROBLEM:
    Naive memory injection dumps ALL experiences into every LLM call.
    500 experiences × 200 tokens = 100,000 tokens per call.
    Cost: Astronomical. Latency: Terrible.
    
    THE SOLUTION:
    InjectMemory produces surgically precise memory injection.
    5 recent experiences × 40 tokens = 200 tokens per call.
    Cost: Minimal. Latency: Fast. Quality: Focused.
    
    Usage:
        # Call this before EVERY LLM invocation
        memory_string = InjectMemory.execute(
            experiences=agent.experiences,
            current_goal=agent.current_task,
            max_tokens=2000
        )
        
        # Inject into prompt
        prompt = f"{memory_string}\\n\\n---\\n\\n{current_task}"
    """
    
    @staticmethod
    def execute(
        experiences: List[Experience],
        current_goal: str = "",
        config: MemoryConfig = None,
        max_tokens: int = 2000
    ) -> str:
        """
        THE TOKEN SAVER.
        
        Instead of dumping all memory (100K+ tokens),
        this produces a surgically precise memory injection
        typically under 2000 tokens.
        
        Call this before every LLM invocation.
        
        Args:
            experiences: List of all past experiences
            current_goal: What the agent is trying to do now
            config: Optional memory configuration
            max_tokens: Maximum tokens to use (default 2000)
        
        Returns:
            Formatted string ready for prompt injection.
            Empty string if no experiences to inject.
        """
        if config is None:
            config = MemoryConfig()
        
        # Handle empty experiences
        if not experiences:
            return ""
        
        # =====================================================================
        # 1. BUDGET
        # =====================================================================
        
        budget = TokenBudget()
        budget.calculate_available()
        
        # Use the smaller of:
        # - Available budget
        # - Configured max
        # - User-specified max
        actual_budget = min(
            budget.available_for_memory,
            config.max_memory_tokens,
            max_tokens
        )
        
        # =====================================================================
        # 2. SELECT (Recent + Relevant)
        # =====================================================================
        
        # Strategy: Take last N experiences that fit budget
        # In Phase 2, we'll add semantic search for relevance
        
        selected: List[CompressedMemory] = []
        tokens_used = 0
        
        # Iterate backwards through recent experiences
        # (most recent first, up to last 20)
        for exp in reversed(experiences[-20:]):
            # Compress this experience
            compressed = CompressExperience.execute(exp, config)
            entry_tokens = compressed.compressed_token_count
            
            # Check if it fits in budget
            if tokens_used + entry_tokens > actual_budget:
                break
            
            selected.append(compressed)
            tokens_used += entry_tokens
        
        # Reverse back to chronological order
        selected.reverse()
        
        # =====================================================================
        # 3. FORMAT
        # =====================================================================
        
        injection = InjectMemory._format_injection(
            selected, tokens_used
        )
        
        return injection

    @staticmethod
    def execute_with_semantic_search(
        experiences: List[Experience],
        compressed_memories: List[CompressedMemory],
        current_goal: str = "",
        config: MemoryConfig = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Token-optimized memory injection WITH semantic search.
        
        Phase 2: Uses semantic similarity to find RELEVANT memories,
        not just RECENT ones.
        
        Args:
            experiences: List of all past experiences
            compressed_memories: List of compressed memories (with embeddings)
            current_goal: What the agent is trying to do now
            config: Optional memory configuration
            max_tokens: Maximum tokens to use (default 2000)
        
        Returns:
            Formatted string ready for prompt injection
        """
        if config is None:
            config = MemoryConfig()
        
        # Handle empty
        if not experiences or not compressed_memories:
            return ""
        
        # =====================================================================
        # 1. BUDGET
        # =====================================================================
        
        budget = TokenBudget()
        budget.calculate_available()
        actual_budget = min(
            budget.available_for_memory,
            config.max_memory_tokens,
            max_tokens
        )
        
        # =====================================================================
        # 2. SEMANTIC SEARCH (Phase 2)
        # =====================================================================
        
        # Build query
        query = MemoryQuery()
        query.query_text = current_goal
        query.max_results = 5
        query.min_relevance = config.min_similarity_threshold
        query.token_budget = actual_budget
        
        # Execute search
        search_result = SemanticSearch.execute(
            query=query,
            compressed_memories=compressed_memories,
            config=config
        )
        
        # =====================================================================
        # 3. FORMAT
        # =====================================================================
        
        injection = search_result.format_for_injection()
        
        return injection
    
    @staticmethod
    def _format_injection(
        compressed_memories: List[CompressedMemory],
        total_tokens: int
    ) -> str:
        """
        Formats compressed memories into a clean prompt-ready string.
        
        Designed for maximum LLM comprehension with minimum tokens.
        
        Format:
            ## Recent Experiences
            - ✓ Task 1 → Result 1 @url1
            - ✗ Task 2 → Result 2 @url2
            - ✓ Task 3 → Result 3 @url3
            [Memory: ~120 tokens]
        
        Args:
            compressed_memories: List of compressed memories
            total_tokens: Total tokens used
        
        Returns:
            Formatted injection string
        """
        if not compressed_memories:
            return ""
        
        sections = []
        
        # Header
        sections.append("## Recent Experiences")
        
        # Add each compressed memory
        for comp in compressed_memories[-5:]:  # Last 5 max
            injection_str = comp.to_injection_string()
            sections.append(f"- {injection_str}")
        
        # Join sections
        result = "\n".join(sections)
        
        # Add token usage footer (helps with debugging)
        result += f"\n[Memory: ~{total_tokens} tokens]"
        
        return result
    
    @staticmethod
    def execute_with_summary(
        experiences: List[Experience],
        current_goal: str = "",
        config: MemoryConfig = None,
        max_tokens: int = 2000
    ) -> dict:
        """
        Execute injection and return detailed summary.
        
        Useful for debugging and monitoring.
        
        Args:
            experiences: List of all past experiences
            current_goal: What the agent is trying to do now
            config: Optional memory configuration
            max_tokens: Maximum tokens to use
        
        Returns:
            Dictionary with injection string and metadata
        """
        if config is None:
            config = MemoryConfig()
        
        # Calculate budget
        budget = TokenBudget()
        budget.calculate_available()
        actual_budget = min(
            budget.available_for_memory,
            config.max_memory_tokens,
            max_tokens
        )
        
        # Compress and select
        selected: List[CompressedMemory] = []
        tokens_used = 0
        
        for exp in reversed(experiences[-20:]):
            compressed = CompressExperience.execute(exp, config)
            entry_tokens = compressed.compressed_token_count
            
            if tokens_used + entry_tokens > actual_budget:
                break
            
            selected.append(compressed)
            tokens_used += entry_tokens
        
        selected.reverse()
        
        # Format
        injection = InjectMemory._format_injection(selected, tokens_used)
        
        # Calculate stats
        original_tokens = sum(
            comp.original_token_count for comp in selected
        )
        compression_ratio = (
            tokens_used / original_tokens
            if original_tokens > 0 else 0
        )
        
        return {
            "injection": injection,
            "memories_injected": len(selected),
            "tokens_used": tokens_used,
            "original_tokens": original_tokens,
            "compression_ratio": compression_ratio,
            "budget_available": actual_budget,
            "budget_utilization": tokens_used / actual_budget if actual_budget > 0 else 0,
        }
