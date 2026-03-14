#!/usr/bin/env python3
"""BuildIndex interaction — build embedding index from experiences.

Creates or updates the memory index by embedding all compressed
memories. Runs periodically, not on every query.

Cost: Zero API tokens (local embeddings)
Time: ~50ms per memory (first run)
Frequency: Once per session, or when memories change significantly
"""

import time
from typing import List, Optional
from smolclaw.agent.entities.MemoryIndex import MemoryIndex
from smolclaw.agent.entities.CompressedMemory import CompressedMemory
from smolclaw.agent.entities.memory.Experience import Experience
from smolclaw.agent.entities.memory.ExperienceMemory import ExperienceMemory
from smolclaw.agent.config.MemoryConfig import MemoryConfig
from smolclaw.agent.interactions.memory_optimization.CompressExperience import (
    CompressExperience
)
from smolclaw.agent.interactions.embedding.GenerateEmbedding import (
    GenerateEmbedding
)
from smolclaw.agent.repositories.MemoryIndexRepository import (
    MemoryIndexRepository
)


class BuildIndex:
    """Build embedding index from experiences.
    
    Flow:
    1. Load existing index (if exists)
    2. Compress new experiences
    3. Embed compressed memories
    4. Add to index
    5. Save index to disk
    
    Cost: Zero API tokens (local embeddings)
    Time: ~50ms per memory (first run), ~5ms per memory (incremental)
    
    Usage:
        # Build from scratch
        index = BuildIndex.execute(experience_memory)
        
        # Incremental update
        index = BuildIndex.execute(experience_memory, existing_index)
    """
    
    @staticmethod
    def execute(
        experience_memory: ExperienceMemory,
        existing_index: Optional[MemoryIndex] = None,
        config: MemoryConfig = None,
        index_file: str = "memory_index.pkl"
    ) -> MemoryIndex:
        """
        Build or update memory index from experiences.
        
        Args:
            experience_memory: Experience memory with all experiences
            existing_index: Existing index to update (optional)
            config: Memory configuration
            index_file: Path to index file for persistence
        
        Returns:
            Built or updated MemoryIndex
        """
        if config is None:
            config = MemoryConfig()
        
        start_time = time.time()
        
        # =====================================================================
        # 1. LOAD EXISTING INDEX
        # =====================================================================
        
        if existing_index is None:
            existing_index = MemoryIndexRepository.load(index_file)
        
        if existing_index:
            print(f"  ✓ Loaded existing index: {existing_index.total_entries} entries")
        else:
            existing_index = MemoryIndex()
            print(f"  ✓ Created new index")
        
        # =====================================================================
        # 2. GET EXPERIENCES
        # =====================================================================
        
        experiences = (
            experience_memory.experiences
            if hasattr(experience_memory, 'experiences')
            else []
        )
        
        if not experiences:
            print(f"  ℹ No experiences to index")
            return existing_index
        
        print(f"  ✓ Found {len(experiences)} experiences")
        
        # =====================================================================
        # 3. COMPRESS NEW EXPERIENCES
        # =====================================================================
        
        # Determine which experiences need indexing
        # (those not already in the index)
        indexed_tasks = set()
        for meta in existing_index.metadata:
            if 'task' in meta:
                indexed_tasks.add(meta['task'])
        
        new_experiences = []
        for exp in experiences:
            if exp.task not in indexed_tasks:
                new_experiences.append(exp)
        
        if not new_experiences:
            print(f"  ℹ All experiences already indexed")
            return existing_index
        
        print(f"  ✓ Compressing {len(new_experiences)} new experiences...")
        
        compressed_memories: List[CompressedMemory] = []
        for exp in new_experiences:
            compressed = CompressExperience.execute(exp, config)
            compressed_memories.append(compressed)
        
        # =====================================================================
        # 4. EMBED COMPRESSED MEMORIES
        # =====================================================================
        
        print(f"  ✓ Embedding {len(compressed_memories)} memories...")
        embed_start = time.time()
        
        embeddings = []
        for mem in compressed_memories:
            embedding = GenerateEmbedding.execute(mem.compressed_summary, config)
            embeddings.append(embedding)
            mem.embedding = embedding  # Store on memory object
        
        embed_elapsed = (time.time() - embed_start) * 1000
        print(f"    Embedding time: {embed_elapsed:.2f}ms "
              f"({embed_elapsed/len(compressed_memories):.2f}ms per memory)")
        
        # =====================================================================
        # 5. ADD TO INDEX
        # =====================================================================
        
        metadatas = []
        for mem, exp in zip(compressed_memories, new_experiences):
            metadata = {
                'task': exp.task,
                'summary': mem.compressed_summary,
                'outcome': mem.outcome,
                'token_count': mem.compressed_token_count,
                'timestamp': mem.timestamp,
                'final_url': exp.final_url if hasattr(exp, 'final_url') else "",
                'success': exp.success if hasattr(exp, 'success') else True,
            }
            metadatas.append(metadata)
        
        added = existing_index.add_entries(embeddings, metadatas)
        print(f"  ✓ Added {added} entries to index")
        
        # =====================================================================
        # 6. SAVE INDEX
        # =====================================================================
        
        MemoryIndexRepository.save(existing_index, index_file)
        
        # =====================================================================
        # 7. STATISTICS
        # =====================================================================
        
        total_elapsed = (time.time() - start_time) * 1000
        stats = existing_index.get_stats()
        
        print(f"\n  Index Statistics:")
        print(f"    Total entries: {stats['total_entries']}")
        print(f"    Dimension: {stats['dimension']}")
        print(f"    Size: {stats['memory_size_mb']:.2f} MB")
        print(f"    Total time: {total_elapsed:.2f}ms")
        
        return existing_index
    
    @staticmethod
    def rebuild_from_scratch(
        experience_memory: ExperienceMemory,
        config: MemoryConfig = None,
        index_file: str = "memory_index.pkl"
    ) -> MemoryIndex:
        """
        Rebuild index from scratch (ignores existing index).
        
        Use this when:
        - Changing embedding model
        - Index is corrupted
        - Want to re-index all experiences
        
        Args:
            experience_memory: Experience memory
            config: Memory configuration
            index_file: Path to index file
        
        Returns:
            Newly built MemoryIndex
        """
        # Delete existing index
        MemoryIndexRepository.delete(index_file)
        
        # Build new index
        return BuildIndex.execute(
            experience_memory=experience_memory,
            existing_index=None,
            config=config,
            index_file=index_file
        )
