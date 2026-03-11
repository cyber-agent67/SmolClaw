#!/usr/bin/env python3
"""CompressedMemory entity — token-efficient memory entry.

Stores experiences in a highly compressed format (40 tokens vs 200 tokens)
while preserving key information needed for agent recall.
"""

from typing import Optional, List


class CompressedMemory:
    """Compressed memory entry for token-efficient storage.
    
    Key Insight: Instead of storing raw 200-token experiences,
    compress to ~40 tokens using extractive summarization.
    
    Compression Ratio: 5x (200 → 40 tokens)
    Method: Extractive (no LLM call needed)
    Cost: Zero API tokens
    
    Example:
        Original (200 tokens):
        "The agent was tasked with finding FDA registration requirements.
        It navigated to fda.gov, clicked through multiple pages, searched
        for 'registration', and eventually found the requirements page at
        /medical-devices/device-registration-and-listing. The task was
        successful and the user was provided with the requirements summary."
        
        Compressed (40 tokens):
        "✓ Find FDA registration requirements → Found requirements page
        @/medical-devices/device-registration-and-listing"
    """
    
    def __init__(self):
        # =====================================================================
        # Core Information
        # =====================================================================
        
        # Original task description (preserved for context)
        self.original_task: str = ""
        
        # Compressed summary (the money shot - ~40 tokens)
        self.compressed_summary: str = ""
        
        # Key actions taken (extracted verb phrases, top 3)
        self.key_actions: List[str] = []
        
        # Outcome indicator (✓ success, ✗ failure)
        self.outcome: str = ""
        
        # =====================================================================
        # Token Statistics
        # =====================================================================
        
        # Token count before compression
        self.original_token_count: int = 0
        
        # Token count after compression
        self.compressed_token_count: int = 0
        
        # Compression ratio (compressed / original)
        # Lower is better (0.2 = 5x compression)
        self.compression_ratio: float = 1.0
        
        # =====================================================================
        # Relevance (Phase 2 - Semantic Search)
        # =====================================================================
        
        # Relevance score for current query (0.0 to 1.0)
        self.relevance_score: float = 0.0
        
        # Embedding vector for semantic search
        self.embedding: Optional[List[float]] = None
        
        # =====================================================================
        # Metadata
        # =====================================================================
        
        # Timestamp of experience (ISO format)
        self.timestamp: str = ""
        
        # Memory tier (hot/warm/cold)
        self.tier: str = "cold"
        
        # Starting URL
        self.start_url: str = ""
        
        # Final URL
        self.final_url: str = ""
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "original_task": self.original_task,
            "compressed_summary": self.compressed_summary,
            "key_actions": self.key_actions,
            "outcome": self.outcome,
            "original_token_count": self.original_token_count,
            "compressed_token_count": self.compressed_token_count,
            "compression_ratio": self.compression_ratio,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp,
            "tier": self.tier,
            "start_url": self.start_url,
            "final_url": self.final_url,
        }
    
    def to_injection_string(self) -> str:
        """
        Format for prompt injection.
        
        Returns:
            Formatted string ready for LLM prompt
        """
        parts = []
        
        # Add outcome icon
        parts.append(f"{self.outcome}")
        
        # Add compressed summary
        parts.append(self.compressed_summary)
        
        # Add URL path if available
        if self.final_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.final_url)
                if parsed.path:
                    parts.append(f"@{parsed.path[:50]}")
            except Exception:
                pass
        
        # Add relevance score if available (Phase 2)
        if self.relevance_score > 0:
            parts.append(f"[{self.relevance_score:.0%}]")
        
        return " ".join(parts)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return self.to_injection_string()
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"CompressedMemory("
            f"outcome={self.outcome}, "
            f"tokens={self.compressed_token_count}, "
            f"ratio={self.compression_ratio:.2f})"
        )
