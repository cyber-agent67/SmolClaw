#!/usr/bin/env python3
"""Memory optimization configuration.

Controls token limits, compression settings, and retrieval parameters
for the token-efficient memory system.
"""


class MemoryConfig:
    """Configuration for token-efficient memory system."""
    
    def __init__(self):
        # =====================================================================
        # Token Limits
        # =====================================================================
        
        # Total context window of the LLM (e.g., GPT-4o = 128K)
        self.total_context_window: int = 128000
        
        # Maximum tokens to use for memory injection
        # This is the hard cap to prevent overflow
        self.max_memory_tokens: int = 8000
        
        # Token allocation per memory tier
        # Hot: Recent session context (full detail)
        self.max_hot_tokens: int = 4000
        # Warm: Semantically relevant past experiences (compressed)
        self.max_warm_tokens: int = 3000
        # Cold: Historical summary (heavily compressed)
        self.max_cold_tokens: int = 1000
        
        # Reserved tokens for other prompt components
        self.reserved_for_system_prompt: int = 2000
        self.reserved_for_user_prompt: int = 2000
        self.reserved_for_tools: int = 3000
        self.reserved_for_response: int = 4000
        self.reserved_for_page_state: int = 8000
        
        # =====================================================================
        # Compression Settings
        # =====================================================================
        
        # Approximate characters per token (for estimation)
        self.approx_chars_per_token: int = 4
        
        # Compress experience after N experiences stored
        self.compress_after_n_experiences: int = 10
        
        # Maximum tokens for compressed summary
        self.max_summary_tokens: int = 200
        
        # Enable progressive summarization
        self.progressive_summarization: bool = True
        
        # =====================================================================
        # Embedding Settings (Phase 2)
        # =====================================================================
        
        # Embedding model to use (local, no API cost)
        self.embedding_model: str = "all-MiniLM-L6-v2"
        
        # Embedding dimension
        self.embedding_dimension: int = 384
        
        # Use local embeddings (True = zero API cost)
        self.use_local_embeddings: bool = True
        
        # =====================================================================
        # Retrieval Settings (Phase 2)
        # =====================================================================
        
        # Maximum number of memories to retrieve
        self.max_retrieval_results: int = 5
        
        # Minimum similarity threshold for retrieval
        self.min_similarity_threshold: float = 0.4
        
        # Enable semantic search
        self.semantic_search_enabled: bool = True
        
        # =====================================================================
        # Eviction Settings (Phase 3)
        # =====================================================================
        
        # Maximum experiences to store
        self.max_stored_experiences: int = 1000
        
        # Evict memories below this relevance score
        self.evict_below_relevance: float = 0.2
        
        # Evict memories older than N days
        self.evict_older_than_days: int = 30
        
        # =====================================================================
        # Deduplication Settings (Phase 3)
        # =====================================================================
        
        # Similarity threshold for deduplication
        # If two memories are >90% similar, keep only one
        self.dedup_similarity_threshold: float = 0.9
    
    def get_available_memory_tokens(self) -> int:
        """
        Calculate tokens available for memory after reserving for other components.
        
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
        return max(self.total_context_window - used, 0)
    
    def get_tier_allocation(self) -> dict:
        """
        Get token allocation per memory tier.
        
        Returns:
            Dictionary with hot/warm/cold token allocations
        """
        available = self.get_available_memory_tokens()
        capped = min(available, self.max_memory_tokens)
        
        return {
            "hot": min(int(capped * 0.6), self.max_hot_tokens),
            "warm": min(int(capped * 0.3), self.max_warm_tokens),
            "cold": min(int(capped * 0.1), self.max_cold_tokens),
        }
