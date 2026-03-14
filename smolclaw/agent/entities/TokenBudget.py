#!/usr/bin/env python3
"""TokenBudget entity — controls how many tokens memory can use.

This entity calculates the exact token budget available for memory
injection after accounting for all other prompt components.
"""

from typing import Dict


class TokenBudget:
    """Token budget calculator for memory injection.
    
    Prevents context window overflow by calculating exact available tokens.
    
    Example:
        budget = TokenBudget()
        budget.total_context_window = 128000
        budget.reserved_for_system_prompt = 2000
        budget.reserved_for_tools = 3000
        # ... set other reservations ...
        
        available = budget.calculate_available()
        # available = 111,000 tokens for memory
    """
    
    def __init__(self):
        # =====================================================================
        # Context Window
        # =====================================================================
        
        # Total context window of the LLM
        # GPT-4o: 128,000 tokens
        # Claude-3: 200,000 tokens
        # Adjust based on your model
        self.total_context_window: int = 128000
        
        # =====================================================================
        # Reserved Tokens (Non-Memory)
        # =====================================================================
        
        # System prompt (agent instructions, personality, etc.)
        self.reserved_for_system_prompt: int = 2000
        
        # User prompt (current task/query)
        self.reserved_for_user_prompt: int = 2000
        
        # Tool definitions (JSON schemas, descriptions)
        self.reserved_for_tools: int = 3000
        
        # Response reserve (space for LLM output)
        self.reserved_for_response: int = 4000
        
        # Page state (current URL, DOM snapshot, etc.)
        self.reserved_for_page_state: int = 8000
        
        # =====================================================================
        # Calculated Values
        # =====================================================================
        
        # Tokens available for memory injection
        self.available_for_memory: int = 0
        
        # Token allocation per tier (hot/warm/cold)
        self.allocated_tiers: Dict[str, int] = {
            "hot": 0,
            "warm": 0,
            "cold": 0
        }
    
    def calculate_available(self) -> int:
        """
        Calculate remaining tokens available for memory injection.
        
        Formula:
            available = total_context_window - sum(reserved_components)
        
        Returns:
            Available tokens for memory injection
        """
        used = (
            self.reserved_for_system_prompt +
            self.reserved_for_user_prompt +
            self.reserved_for_tools +
            self.reserved_for_response +
            self.reserved_for_page_state
        )
        
        self.available_for_memory = max(
            self.total_context_window - used, 0
        )
        
        # Distribute across tiers
        # Hot: 60% (recent session context)
        # Warm: 30% (relevant past experiences)
        # Cold: 10% (historical summary)
        self.allocated_tiers["hot"] = int(
            self.available_for_memory * 0.6
        )
        self.allocated_tiers["warm"] = int(
            self.available_for_memory * 0.3
        )
        self.allocated_tiers["cold"] = int(
            self.available_for_memory * 0.1
        )
        
        return self.available_for_memory
    
    def get_tier_allocation(self) -> Dict[str, int]:
        """
        Get token allocation per memory tier.
        
        Returns:
            Dictionary with hot/warm/cold allocations
        """
        if self.available_for_memory == 0:
            self.calculate_available()
        
        return self.allocated_tiers.copy()
    
    def get_summary(self) -> str:
        """
        Get human-readable summary of token budget.
        
        Returns:
            Formatted string with budget breakdown
        """
        if self.available_for_memory == 0:
            self.calculate_available()
        
        used = (
            self.reserved_for_system_prompt +
            self.reserved_for_user_prompt +
            self.reserved_for_tools +
            self.reserved_for_response +
            self.reserved_for_page_state
        )
        
        summary = f"""
Token Budget Summary
====================
Total Context Window: {self.total_context_window:,} tokens

Reserved:
  - System Prompt:     {self.reserved_for_system_prompt:,} tokens
  - User Prompt:       {self.reserved_for_user_prompt:,} tokens
  - Tools:             {self.reserved_for_tools:,} tokens
  - Response:          {self.reserved_for_response:,} tokens
  - Page State:        {self.reserved_for_page_state:,} tokens
  ────────────────────────────────────────
  Total Reserved:      {used:,} tokens

Available for Memory:  {self.available_for_memory:,} tokens

Tier Allocation:
  - Hot (60%):         {self.allocated_tiers['hot']:,} tokens
  - Warm (30%):        {self.allocated_tiers['warm']:,} tokens
  - Cold (10%):        {self.allocated_tiers['cold']:,} tokens
""".strip()
        
        return summary
    
    def is_within_budget(self, proposed_tokens: int) -> bool:
        """
        Check if proposed token count is within budget.
        
        Args:
            proposed_tokens: Number of tokens to check
        
        Returns:
            True if within budget, False otherwise
        """
        if self.available_for_memory == 0:
            self.calculate_available()
        
        return proposed_tokens <= self.available_for_memory
    
    def get_utilization(self, used_tokens: int) -> float:
        """
        Calculate budget utilization percentage.
        
        Args:
            used_tokens: Number of tokens actually used
        
        Returns:
            Utilization percentage (0.0 to 1.0)
        """
        if self.available_for_memory == 0:
            self.calculate_available()
        
        if self.available_for_memory == 0:
            return 0.0
        
        return min(used_tokens / self.available_for_memory, 1.0)
