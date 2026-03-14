#!/usr/bin/env python3
"""EvictStale interaction — remove old/low-value memories.

Actively forgets memories that are:
- Older than N days
- Below relevance threshold
- Exceeding storage limit

Keeps the memory index lean and relevant.

Cost: Zero API tokens (pure filtering)
Time: O(n) for n memories
Savings: Prevents unbounded growth
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Set
from smolclaw.agent.entities.MemoryIndex import MemoryIndex
from smolclaw.agent.config.MemoryConfig import MemoryConfig
from smolclaw.agent.repositories.MemoryIndexRepository import (
    MemoryIndexRepository
)


class EvictStale:
    """Evict stale/low-value memories from index.
    
    Eviction Criteria:
    1. Age: Older than N days (default: 30)
    2. Relevance: Below threshold (default: 0.2)
    3. Count: Exceeding max (default: 1000)
    
    Strategy:
    1. Scan all memories
    2. Mark for eviction based on criteria
    3. Remove marked memories
    4. Save updated index
    
    Cost: Zero API tokens
    Time: O(n)
    Savings: Prevents unbounded growth
    
    Usage:
        # Evict stale memories
        stats = EvictStale.execute(index)
        
        # Custom eviction policy
        stats = EvictStale.execute(
            index,
            older_than_days=60,
            max_entries=500
        )
    """
    
    @staticmethod
    def execute(
        index: MemoryIndex,
        config: MemoryConfig = None,
        older_than_days: int = None,
        max_entries: int = None,
        save: bool = True,
        index_file: str = "memory_index.pkl"
    ) -> Dict:
        """
        Evict stale/low-value memories from index.
        
        Args:
            index: MemoryIndex to evict from
            config: Memory configuration
            older_than_days: Evict memories older than N days
            max_entries: Maximum entries to keep
            save: Whether to save updated index
            index_file: Path to index file
        
        Returns:
            Dictionary with eviction statistics
        """
        if config is None:
            config = MemoryConfig()
        
        # Use config defaults if not specified
        if older_than_days is None:
            older_than_days = config.evict_older_than_days
        if max_entries is None:
            max_entries = config.max_stored_experiences
        
        start_time = time.time()
        
        if index.total_entries == 0:
            return {
                'evicted': 0,
                'remaining': 0,
                'time_ms': 0,
                'reasons': {}
            }
        
        print(f"  ✓ Evicting stale memories from {index.total_entries} entries...")
        print(f"    Age threshold: {older_than_days} days")
        print(f"    Max entries: {max_entries}")
        
        # =====================================================================
        # 1. FIND MEMORIES TO EVICT
        # =====================================================================
        
        to_remove: Set[int] = set()
        reasons: Dict[str, int] = {
            'age': 0,
            'count': 0,
        }
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        for i, meta in enumerate(index.metadata):
            # Check age
            timestamp_str = meta.get('timestamp', '')
            if timestamp_str:
                try:
                    ts = datetime.fromisoformat(timestamp_str)
                    if ts < cutoff_date:
                        to_remove.add(i)
                        reasons['age'] += 1
                        continue
                except Exception:
                    pass
            
            # Check relevance (if stored)
            relevance = meta.get('relevance_score', 1.0)
            if relevance < config.evict_below_relevance:
                if i not in to_remove:
                    to_remove.add(i)
        
        # If still over limit, remove oldest first
        if len(index.metadata) - len(to_remove) > max_entries:
            excess = len(index.metadata) - len(to_remove) - max_entries
            
            # Get indices not already marked
            remaining = [
                i for i in range(len(index.metadata))
                if i not in to_remove
            ]
            
            # Sort by timestamp (oldest first)
            def get_timestamp(idx):
                return index.metadata[idx].get('timestamp', '')
            
            remaining.sort(key=get_timestamp)
            
            # Mark oldest for removal
            for idx in remaining[:excess]:
                to_remove.add(idx)
                reasons['count'] += 1
        
        # =====================================================================
        # 2. REMOVE MEMORIES
        # =====================================================================
        
        if to_remove:
            removed = index.remove_entries(list(to_remove))
            print(f"  ✓ Evicted {removed} memories")
        else:
            removed = 0
            print(f"  ✓ No memories to evict")
        
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
        
        stats = {
            'evicted': removed,
            'remaining': index.total_entries,
            'time_ms': elapsed,
            'reasons': reasons,
            'older_than_days': older_than_days,
            'max_entries': max_entries,
        }
        
        print(f"\n  Eviction Statistics:")
        print(f"    Evicted: {stats['evicted']}")
        print(f"    Remaining: {stats['remaining']}")
        print(f"    By age: {reasons['age']}")
        print(f"    By count: {reasons['count']}")
        print(f"    Time: {elapsed:.2f}ms")
        
        return stats
    
    @staticmethod
    def get_eviction_candidates(
        index: MemoryIndex,
        older_than_days: int = 30,
        max_entries: int = 1000
    ) -> List[Dict]:
        """
        Get list of memories that would be evicted (without removing).
        
        Args:
            index: MemoryIndex to scan
            older_than_days: Age threshold
            max_entries: Max entries to keep
        
        Returns:
            List of eviction candidates with reasons
        """
        candidates = []
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        for i, meta in enumerate(index.metadata):
            reason = None
            
            # Check age
            timestamp_str = meta.get('timestamp', '')
            if timestamp_str:
                try:
                    ts = datetime.fromisoformat(timestamp_str)
                    if ts < cutoff_date:
                        reason = 'age'
                except Exception:
                    pass
            
            if reason:
                candidates.append({
                    'index': i,
                    'reason': reason,
                    'task': meta.get('task', 'Unknown')[:50],
                    'timestamp': timestamp_str,
                })
        
        # If over limit, add oldest
        if len(index.metadata) > max_entries:
            excess = len(index.metadata) - max_entries
            
            # Sort by timestamp
            sorted_indices = sorted(
                range(len(index.metadata)),
                key=lambda i: index.metadata[i].get('timestamp', '')
            )
            
            for idx in sorted_indices[:excess]:
                if not any(c['index'] == idx for c in candidates):
                    candidates.append({
                        'index': idx,
                        'reason': 'count',
                        'task': index.metadata[idx].get('task', 'Unknown')[:50],
                        'timestamp': index.metadata[idx].get('timestamp', ''),
                    })
        
        return candidates
