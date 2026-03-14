#!/usr/bin/env python3
"""SummarizeHistory interaction — progressive summarization.

Maintains a running summary of all experiences instead of storing
each one individually. Reduces memory from O(n) to O(1).

Key Insight: Instead of storing 500 raw experiences (~100K tokens),
maintain a RUNNING SUMMARY (~200 tokens) that gets updated incrementally.

Cost: Zero LLM tokens (heuristic compression)
Time: O(1) per update
Savings: 99%+ for large experience counts
"""

from datetime import datetime
from typing import Optional
from smolclaw.agent.entities.CompressedMemory import CompressedMemory
from smolclaw.agent.entities.memory.Experience import Experience
from smolclaw.agent.config.MemoryConfig import MemoryConfig


class MemorySummary:
    """Progressive summary of experience history.
    
    Instead of storing all experiences individually,
    maintain a running summary that gets updated incrementally.
    
    Structure:
        running_summary: Concatenated summary of all experiences
        total_experiences: Count of experiences summarized
        last_updated: Timestamp of last update
        token_count: Current token count
    """
    
    def __init__(self):
        self.running_summary: str = ""
        self.total_experiences: int = 0
        self.last_updated: str = datetime.now().isoformat()
        self.token_count: int = 0
        self.summary_level: int = 0  # Number of times compressed
    
    def to_dict(self) -> dict:
        return {
            'running_summary': self.running_summary,
            'total_experiences': self.total_experiences,
            'last_updated': self.last_updated,
            'token_count': self.token_count,
            'summary_level': self.summary_level,
        }


class SummarizeHistory:
    """Progressive summarization of experience history.
    
    Flow:
    1. Compress new experience to ~40 tokens
    2. Append to running summary
    3. If summary > max_tokens, compress the summary itself
    4. Keep only patterns and recent entries
    
    Cost: Zero LLM tokens (heuristic)
    Time: O(1) per update
    Savings: 99%+ for 1000+ experiences
    
    Usage:
        summary = MemorySummary()
        
        # Add each experience
        for exp in experiences:
            compressed = CompressExperience.execute(exp)
            summary = SummarizeHistory.execute(summary, compressed)
        
        # Get summary for injection
        injection = summary.running_summary
    """
    
    @staticmethod
    def execute(
        existing_summary: MemorySummary,
        new_experience: CompressedMemory,
        config: MemoryConfig = None
    ) -> MemorySummary:
        """
        Incrementally update running summary with new experience.
        
        Args:
            existing_summary: Current running summary
            new_experience: New compressed experience to add
            config: Memory configuration
        
        Returns:
            Updated MemorySummary
        """
        if config is None:
            config = MemoryConfig()
        
        summary = MemorySummary()
        summary.total_experiences = existing_summary.total_experiences + 1
        summary.last_updated = datetime.now().isoformat()
        summary.summary_level = existing_summary.summary_level
        
        # =====================================================================
        # 1. BUILD INCREMENTAL SUMMARY
        # =====================================================================
        
        existing = existing_summary.running_summary or ""
        
        # Format new entry
        # [N] ✓/✗ Task → Result @URL
        new_entry = (
            f"[{summary.total_experiences}] "
            f"{new_experience.outcome} "
            f"{new_experience.original_task[:80]} → "
            f"{str(new_experience.compressed_summary)[-60:]}"
        )
        
        # Combine
        if existing:
            combined = f"{existing}\n{new_entry}"
        else:
            combined = new_entry
        
        # =====================================================================
        # 2. CHECK TOKEN LIMIT
        # =====================================================================
        
        combined_tokens = len(combined) // config.approx_chars_per_token
        
        if combined_tokens > config.max_summary_tokens:
            # Need to compress
            combined = SummarizeHistory._compress_summary(
                combined,
                config.max_summary_tokens,
                config.approx_chars_per_token
            )
            summary.summary_level += 1
        
        # =====================================================================
        # 3. UPDATE SUMMARY
        # =====================================================================
        
        summary.running_summary = combined.strip()
        summary.token_count = len(summary.running_summary) // config.approx_chars_per_token
        
        return summary
    
    @staticmethod
    def _compress_summary(
        text: str,
        max_tokens: int,
        chars_per_token: int = 4
    ) -> str:
        """
        Compress summary by keeping only recent and pattern-revealing entries.
        
        Heuristic (no LLM):
        1. Keep first line (oldest context)
        2. Keep last N lines (most recent)
        3. Add count of compressed entries
        
        Args:
            text: Summary text to compress
            max_tokens: Maximum tokens allowed
            chars_per_token: Characters per token estimate
        
        Returns:
            Compressed summary
        """
        lines = text.strip().split('\n')
        max_chars = max_tokens * chars_per_token
        
        # If already short enough, return as-is
        if len(lines) <= 5 or len(text) <= max_chars:
            return text
        
        # Calculate how many to keep
        keep_first = 1  # Keep oldest for context
        keep_last = 4   # Keep most recent
        
        compressed_count = len(lines) - keep_first - keep_last
        
        # Build compressed version
        kept = []
        
        # First line (oldest)
        kept.append(lines[0])
        
        # Compression indicator
        if compressed_count > 0:
            kept.append(f"[... {compressed_count} earlier experiences ...]")
        
        # Last N lines (most recent)
        kept.extend(lines[-keep_last:])
        
        result = '\n'.join(kept)
        
        # Final truncation if still too long
        if len(result) > max_chars:
            result = result[:max_chars - 3] + "..."
        
        return result
    
    @staticmethod
    def from_experiences(
        experiences: list,
        config: MemoryConfig = None
    ) -> MemorySummary:
        """
        Build summary from scratch from list of experiences.
        
        Args:
            experiences: List of Experience entities
            config: Memory configuration
        
        Returns:
            Built MemorySummary
        """
        from smolclaw.agent.interactions.memory_optimization.CompressExperience import (
            CompressExperience
        )
        
        if config is None:
            config = MemoryConfig()
        
        summary = MemorySummary()
        
        for exp in experiences:
            compressed = CompressExperience.execute(exp, config)
            summary = SummarizeHistory.execute(summary, compressed, config)
        
        return summary
    
    @staticmethod
    def get_injection_string(summary: MemorySummary) -> str:
        """
        Format summary for prompt injection.
        
        Args:
            summary: MemorySummary to format
        
        Returns:
            Formatted string for LLM prompt
        """
        if not summary.running_summary:
            return ""
        
        injection = "## Historical Summary\n\n"
        injection += summary.running_summary
        injection += f"\n\n[Summary: ~{summary.token_count} tokens | "
        injection += f"{summary.total_experiences} experiences | "
        injection += f"level {summary.summary_level}]"
        
        return injection
