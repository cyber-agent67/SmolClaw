#!/usr/bin/env python3
"""MemoryQuery entity — query for semantic memory retrieval.

Defines the search query for finding relevant past experiences
using semantic similarity.
"""

from typing import Optional, List


class MemoryQuery:
    """Semantic search query for memory retrieval.
    
    Used to find relevant past experiences based on semantic
    similarity rather than just recency.
    
    Example:
        query = MemoryQuery()
        query.query_text = "Find FDA registration requirements"
        query.max_results = 5
        query.min_relevance = 0.4
        query.token_budget = 2000
        
        results = SemanticSearch.execute(query, compressed_memories)
    """
    
    def __init__(self):
        # =====================================================================
        # Query Definition
        # =====================================================================
        
        # Text to search for (current task/goal)
        self.query_text: str = ""
        
        # Pre-computed embedding (optional, computed if not provided)
        self.query_embedding: Optional[List[float]] = None
        
        # =====================================================================
        # Search Parameters
        # =====================================================================
        
        # Maximum number of results to return
        self.max_results: int = 5
        
        # Minimum similarity threshold (0.0 to 1.0)
        # Memories below this score are filtered out
        self.min_relevance: float = 0.4
        
        # Token budget for retrieved memories
        # Search stops when this budget is exhausted
        self.token_budget: int = 2000
        
        # =====================================================================
        # Filters (Optional)
        # =====================================================================
        
        # Filter by memory tier (hot/warm/cold)
        self.tier_filter: Optional[str] = None
        
        # Filter by success/failure
        self.outcome_filter: Optional[str] = None  # "success" or "failure"
        
        # Filter by timestamp (ISO format)
        self.timestamp_after: Optional[str] = None
        
        # =====================================================================
        # Results (Populated after search)
        # =====================================================================
        
        # Number of memories scanned
        self.memories_scanned: int = 0
        
        # Number of memories matched
        self.memories_matched: int = 0
        
        # Search time in milliseconds
        self.search_time_ms: float = 0.0
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "query_text": self.query_text,
            "query_embedding": self.query_embedding,
            "max_results": self.max_results,
            "min_relevance": self.min_relevance,
            "token_budget": self.token_budget,
            "tier_filter": self.tier_filter,
            "outcome_filter": self.outcome_filter,
            "timestamp_after": self.timestamp_after,
            "memories_scanned": self.memories_scanned,
            "memories_matched": self.memories_matched,
            "search_time_ms": self.search_time_ms,
        }
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"MemoryQuery(text='{self.query_text[:50]}...', "
            f"max_results={self.max_results}, "
            f"min_relevance={self.min_relevance})"
        )
