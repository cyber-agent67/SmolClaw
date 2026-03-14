#!/usr/bin/env python3
"""Deduplicate interaction — remove near-duplicate memories.

Finds and removes memories that are >90% similar to each other.
Prevents index bloat and improves search quality.

Cost: Zero API tokens (pure cosine similarity)
Time: ~10ms per comparison
Savings: Typically 10-30% of index size
"""

import time
from typing import List, Dict, Set
from smolclaw.agent.entities.MemoryIndex import MemoryIndex
from smolclaw.agent.config.MemoryConfig import MemoryConfig
from smolclaw.agent.interactions.embedding.ComputeSimilarity import (
    ComputeSimilarity
)
from smolclaw.agent.repositories.MemoryIndexRepository import (
    MemoryIndexRepository
)


class Deduplicate:
    """Remove near-duplicate memories from index.
    
    Strategy:
    1. Compute pairwise similarity for all memories
    2. If similarity > threshold (0.9), mark older one for removal
    3. Remove marked memories from index
    4. Save updated index
    
    Cost: Zero API tokens (pure math)
    Time: O(n²) but fast for n<10000
    Savings: 10-30% typical
    
    Usage:
        # Deduplicate existing index
        stats = Deduplicate.execute(index)
        
        # Deduplicate with custom threshold
        stats = Deduplicate.execute(index, threshold=0.95)
    """
    
    @staticmethod
    def execute(
        index: MemoryIndex,
        config: MemoryConfig = None,
        threshold: float = 0.9,
        save: bool = True,
        index_file: str = "memory_index.pkl"
    ) -> Dict:
        """
        Remove near-duplicate entries from index.
        
        Args:
            index: MemoryIndex to deduplicate
            config: Memory configuration
            threshold: Similarity threshold (0.9 = 90% similar)
            save: Whether to save updated index
            index_file: Path to index file
        
        Returns:
            Dictionary with deduplication statistics
        """
        if config is None:
            config = MemoryConfig()
        
        start_time = time.time()
        
        if len(index.embeddings) < 2:
            return {
                'removed': 0,
                'remaining': index.total_entries,
                'time_ms': 0,
                'savings_percent': 0
            }
        
        print(f"  ✓ Deduplicating {index.total_entries} entries...")
        print(f"    Threshold: {threshold:.0%} similarity")
        
        # =====================================================================
        # 1. FIND DUPLICATES
        # =====================================================================
        
        to_remove: Set[int] = set()
        comparisons = 0
        
        for i in range(len(index.embeddings)):
            if i in to_remove:
                continue
            
            for j in range(i + 1, len(index.embeddings)):
                if j in to_remove:
                    continue
                
                # Compute similarity
                similarity = ComputeSimilarity.execute(
                    index.embeddings[i],
                    index.embeddings[j]
                )
                comparisons += 1
                
                # If highly similar, remove the older one (higher index)
                if similarity >= threshold:
                    to_remove.add(j)
                    
                    # Log for debugging
                    if len(to_remove) <= 5:
                        task_i = index.metadata[i].get('task', 'Unknown')[:50]
                        task_j = index.metadata[j].get('task', 'Unknown')[:50]
                        print(f"    Duplicate found: {similarity:.0%}")
                        print(f"      Keep:  [{i}] {task_i}...")
                        print(f"      Remove: [{j}] {task_j}...")
        
        # =====================================================================
        # 2. REMOVE DUPLICATES
        # =====================================================================
        
        if to_remove:
            removed = index.remove_entries(list(to_remove))
            print(f"  ✓ Removed {removed} duplicates")
        else:
            removed = 0
            print(f"  ✓ No duplicates found")
        
        # =====================================================================
        # 3. SAVE UPDATED INDEX
        # =====================================================================
        
        if save and removed > 0:
            MemoryIndexRepository.save(index, index_file)
            print(f"  ✓ Saved updated index")
        
        # =====================================================================
        # 4. STATISTICS
        # =====================================================================
        
        elapsed = (time.time() - start_time) * 1000
        savings = (removed / index.total_entries * 100) if index.total_entries > 0 else 0
        
        stats = {
            'removed': removed,
            'remaining': index.total_entries,
            'comparisons': comparisons,
            'time_ms': elapsed,
            'savings_percent': savings,
            'threshold': threshold,
        }
        
        print(f"\n  Deduplication Statistics:")
        print(f"    Removed: {removed} entries")
        print(f"    Remaining: {stats['remaining']} entries")
        print(f"    Comparisons: {stats['comparisons']}")
        print(f"    Time: {elapsed:.2f}ms")
        print(f"    Savings: {savings:.1f}%")
        
        return stats
    
    @staticmethod
    def find_duplicates(
        index: MemoryIndex,
        threshold: float = 0.9
    ) -> List[Dict]:
        """
        Find duplicate pairs without removing them.
        
        Args:
            index: MemoryIndex to scan
            threshold: Similarity threshold
        
        Returns:
            List of duplicate pairs with similarity scores
        """
        duplicates = []
        
        for i in range(len(index.embeddings)):
            for j in range(i + 1, len(index.embeddings)):
                similarity = ComputeSimilarity.execute(
                    index.embeddings[i],
                    index.embeddings[j]
                )
                
                if similarity >= threshold:
                    duplicates.append({
                        'index_a': i,
                        'index_b': j,
                        'similarity': similarity,
                        'task_a': index.metadata[i].get('task', 'Unknown')[:50],
                        'task_b': index.metadata[j].get('task', 'Unknown')[:50],
                    })
        
        return duplicates
