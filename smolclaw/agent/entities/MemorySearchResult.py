#!/usr/bin/env python3
"""MemorySearchResult entity — result of semantic memory search.

Contains the results of a semantic search query, including
ranked memories and token usage statistics.
"""

from typing import List
from smolclaw.agent.entities.CompressedMemory import CompressedMemory


class MemorySearchResult:
    """Result of semantic memory search.
    
    Contains ranked memories based on semantic similarity
    to the query, along with token usage statistics.
    
    Example:
        result = SemanticSearch.execute(query, compressed_memories)
        
        print(f"Found {len(result.results)} relevant memories")
        print(f"Total tokens: {result.total_tokens_used}")
        
        for memory in result.results:
            print(f"  [{memory.relevance_score:.0%}] {memory.compressed_summary}")
    """
    
    def __init__(self):
        # =====================================================================
        # Search Results
        # =====================================================================
        
        # Ranked list of relevant memories (highest relevance first)
        self.results: List[CompressedMemory] = []
        
        # =====================================================================
        # Token Statistics
        # =====================================================================
        
        # Total tokens used by all results
        self.total_tokens_used: int = 0
        
        # =====================================================================
        # Query Information
        # =====================================================================
        
        # Original query text
        self.query_text: str = ""
        
        # =====================================================================
        # Formatted Output
        # =====================================================================
        
        # Formatted string ready for prompt injection
        self.formatted_injection: str = ""
    
    def add_result(self, memory: CompressedMemory) -> None:
        """
        Add a memory result to the search results.
        
        Args:
            memory: CompressedMemory to add
        """
        self.results.append(memory)
        self.total_tokens_used += memory.compressed_token_count
    
    def get_top_results(self, n: int = 5) -> List[CompressedMemory]:
        """
        Get top N results by relevance score.
        
        Args:
            n: Number of results to return
        
        Returns:
            List of top N CompressedMemory entities
        """
        # Sort by relevance score (descending)
        sorted_results = sorted(
            self.results,
            key=lambda m: m.relevance_score,
            reverse=True
        )
        
        return sorted_results[:n]
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "results": [r.to_dict() for r in self.results],
            "total_tokens_used": self.total_tokens_used,
            "query_text": self.query_text,
            "formatted_injection": self.formatted_injection,
            "result_count": len(self.results),
        }
    
    def format_for_injection(self) -> str:
        """
        Format search results for prompt injection.
        
        Returns:
            Formatted string ready for LLM prompt
        """
        if not self.results:
            return ""
        
        sections = []
        
        # Header
        sections.append("## Relevant Past Experiences")
        
        # Add each result with relevance score
        for memory in self.get_top_results(5):
            injection_str = memory.to_injection_string()
            relevance = f"[{memory.relevance_score:.0%}]"
            sections.append(f"- {relevance} {injection_str}")
        
        # Join sections
        self.formatted_injection = "\n".join(sections)
        
        # Add token usage footer
        self.formatted_injection += (
            f"\n[Memory: ~{self.total_tokens_used} tokens | "
            f"{len(self.results)} relevant]"
        )
        
        return self.formatted_injection
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"MemorySearchResult("
            f"query='{self.query_text[:50]}...', "
            f"results={len(self.results)}, "
            f"tokens={self.total_tokens_used})"
        )
    
    def __len__(self) -> int:
        """Return number of results."""
        return len(self.results)
