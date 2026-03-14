#!/usr/bin/env python3
"""SemanticSearch interaction — find relevant memories (zero API cost).

Finds the most relevant past experiences using semantic similarity.
Combines embedding generation + cosine similarity for retrieval.

Cost Breakdown:
- Embedding: Local model ($0.00)
- Similarity: Pure math ($0.00)
- Retrieval: Array lookup ($0.00)
- Total: $0.00 per search

Speed:
- Embedding: ~50ms
- Similarity (100 memories): ~10ms
- Total: <100ms
"""

import time
from typing import List
from smolclaw.agent.entities.MemoryQuery import MemoryQuery
from smolclaw.agent.entities.MemorySearchResult import MemorySearchResult
from smolclaw.agent.entities.CompressedMemory import CompressedMemory
from smolclaw.agent.config.MemoryConfig import MemoryConfig
from smolclaw.agent.interactions.embedding.GenerateEmbedding import GenerateEmbedding
from smolclaw.agent.interactions.embedding.ComputeSimilarity import ComputeSimilarity


class SemanticSearch:
    """Semantic search over compressed memories.
    
    Finds relevant past experiences using semantic similarity
    rather than just recency.
    
    Flow:
    1. Embed query (local model, free)
    2. Embed all memories (local model, free)
    3. Compute similarities (pure math, free)
    4. Filter by threshold (free)
    5. Sort by relevance (free)
    6. Return top results within budget (free)
    
    Total Cost: $0.00
    Total Time: <100ms for 100 memories
    
    Usage:
        query = MemoryQuery()
        query.query_text = "Find FDA registration requirements"
        query.max_results = 5
        query.min_relevance = 0.4
        query.token_budget = 2000
        
        result = SemanticSearch.execute(query, compressed_memories)
        
        print(f"Found {len(result)} relevant memories")
        for memory in result.results:
            print(f"  [{memory.relevance_score:.0%}] {memory.compressed_summary}")
    """
    
    @staticmethod
    def execute(
        query: MemoryQuery,
        compressed_memories: List[CompressedMemory],
        config: MemoryConfig = None
    ) -> MemorySearchResult:
        """
        Find relevant memories using semantic similarity.
        
        Args:
            query: MemoryQuery with search parameters
            compressed_memories: List of compressed memories to search
            config: Optional memory configuration
        
        Returns:
            MemorySearchResult with ranked relevant memories
        """
        if config is None:
            config = MemoryConfig()
        
        # Start timing
        start_time = time.time()
        
        # Initialize result
        result = MemorySearchResult()
        result.query_text = query.query_text
        
        # Handle empty memories
        if not compressed_memories:
            result.formatted_injection = ""
            return result
        
        # =====================================================================
        # 1. EMBED QUERY (local model, free)
        # =====================================================================
        
        if query.query_embedding is None:
            query.query_embedding = GenerateEmbedding.execute(
                query.query_text,
                config
            )
        
        # =====================================================================
        # 2. EMBED MEMORIES (if not already embedded)
        # =====================================================================
        
        # Check if memories have embeddings
        memories_with_embeddings = []
        embeddings = []
        metadata = []
        
        for memory in compressed_memories:
            # Skip if tier filter doesn't match
            if query.tier_filter and memory.tier != query.tier_filter:
                continue
            
            # Skip if outcome filter doesn't match
            if query.outcome_filter:
                is_success = memory.outcome == "✓"
                if query.outcome_filter == "success" and not is_success:
                    continue
                if query.outcome_filter == "failure" and is_success:
                    continue
            
            # Get or compute embedding
            if memory.embedding is None:
                # Compute embedding
                memory.embedding = GenerateEmbedding.execute(
                    memory.compressed_summary,
                    config
                )
            
            memories_with_embeddings.append(memory)
            embeddings.append(memory.embedding)
            metadata.append({
                "memory": memory,
                "index": len(memories_with_embeddings) - 1
            })
        
        query.memories_scanned = len(memories_with_embeddings)
        
        # =====================================================================
        # 3. COMPUTE SIMILARITIES (pure math, free)
        # =====================================================================
        
        scored = []
        
        for i, (memory, embedding) in enumerate(zip(memories_with_embeddings, embeddings)):
            similarity = ComputeSimilarity.execute(
                query.query_embedding,
                embedding
            )
            
            # Filter by threshold
            if similarity >= query.min_relevance:
                scored.append({
                    "memory": memory,
                    "similarity": similarity
                })
        
        query.memories_matched = len(scored)
        
        # =====================================================================
        # 4. SORT BY RELEVANCE
        # =====================================================================
        
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        
        # =====================================================================
        # 5. BUDGET-AWARE SELECTION
        # =====================================================================
        
        tokens_used = 0
        
        for item in scored[:query.max_results]:
            memory = item["memory"]
            entry_tokens = memory.compressed_token_count
            
            # Check token budget
            if tokens_used + entry_tokens > query.token_budget:
                break
            
            # Set relevance score on memory
            memory.relevance_score = item["similarity"]
            
            # Add to result
            result.add_result(memory)
            tokens_used += entry_tokens
        
        # =====================================================================
        # 6. FORMAT FOR INJECTION
        # =====================================================================
        
        result.format_for_injection()
        
        # Record timing
        elapsed = time.time() - start_time
        query.search_time_ms = elapsed * 1000
        
        return result
    
    @staticmethod
    def execute_simple(
        query_text: str,
        compressed_memories: List[CompressedMemory],
        max_results: int = 5,
        min_relevance: float = 0.4,
        token_budget: int = 2000,
        config: MemoryConfig = None
    ) -> MemorySearchResult:
        """
        Simplified semantic search interface.
        
        Args:
            query_text: Text to search for
            compressed_memories: List of memories to search
            max_results: Maximum results to return
            min_relevance: Minimum similarity threshold
            token_budget: Maximum tokens to use
            config: Optional memory configuration
        
        Returns:
            MemorySearchResult with ranked memories
        """
        # Build query object
        query = MemoryQuery()
        query.query_text = query_text
        query.max_results = max_results
        query.min_relevance = min_relevance
        query.token_budget = token_budget
        
        # Execute search
        return SemanticSearch.execute(query, compressed_memories, config)
