#!/usr/bin/env python3
"""MemoryIndex entity — embedding-based index for fast retrieval.

Stores embeddings and metadata for efficient semantic search
over large numbers of memories (1000+).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class MemoryIndex:
    """Embedding-based memory index for fast semantic search.
    
    Optimized for:
    - 1000+ memories
    - Fast similarity search
    - Persistent storage
    - Incremental updates
    
    Structure:
        embeddings: List of embedding vectors
        metadata: List of metadata dicts (parallel to embeddings)
        dimension: Embedding dimension (e.g., 384)
        total_entries: Number of indexed memories
    
    Example:
        index = MemoryIndex()
        index.embeddings = [[0.1, 0.2, ...], ...]
        index.metadata = [{'task': '...', 'timestamp': '...'}, ...]
        index.total_entries = len(index.embeddings)
    """
    
    def __init__(self):
        # =====================================================================
        # Core Data
        # =====================================================================
        
        # List of embedding vectors (parallel to metadata)
        self.embeddings: List[List[float]] = []
        
        # List of metadata dicts (parallel to embeddings)
        # Each dict contains: task, summary, timestamp, token_count, etc.
        self.metadata: List[Dict[str, Any]] = []
        
        # =====================================================================
        # Configuration
        # =====================================================================
        
        # Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
        self.dimension: int = 384
        
        # =====================================================================
        # Statistics
        # =====================================================================
        
        # Total number of indexed memories
        self.total_entries: int = 0
        
        # Index creation timestamp
        self.created_at: str = datetime.now().isoformat()
        
        # Last update timestamp
        self.updated_at: str = self.created_at
        
        # =====================================================================
        # Persistence
        # =====================================================================
        
        # File path for persistence
        self.index_file: str = "memory_index.pkl"
    
    def add_entry(
        self,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> int:
        """
        Add a single entry to the index.
        
        Args:
            embedding: Embedding vector
            metadata: Metadata dictionary
        
        Returns:
            Index of the added entry
        """
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: "
                f"expected {self.dimension}, got {len(embedding)}"
            )
        
        self.embeddings.append(embedding)
        self.metadata.append(metadata)
        self.total_entries += 1
        self.updated_at = datetime.now().isoformat()
        
        return self.total_entries - 1
    
    def add_entries(
        self,
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple entries to the index (batch).
        
        Args:
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
        
        Returns:
            Number of entries added
        """
        if len(embeddings) != len(metadatas):
            raise ValueError(
                f"Embeddings and metadatas must have same length"
            )
        
        for embedding in embeddings:
            if len(embedding) != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: "
                    f"expected {self.dimension}, got {len(embedding)}"
                )
        
        self.embeddings.extend(embeddings)
        self.metadata.extend(metadatas)
        self.total_entries += len(embeddings)
        self.updated_at = datetime.now().isoformat()
        
        return len(embeddings)
    
    def remove_entries(self, indices: List[int]) -> int:
        """
        Remove entries by index (for deduplication/eviction).
        
        Args:
            indices: List of indices to remove
        
        Returns:
            Number of entries removed
        """
        if not indices:
            return 0
        
        # Sort indices in reverse order to remove from end first
        indices = sorted(set(indices), reverse=True)
        
        removed = 0
        for idx in indices:
            if 0 <= idx < len(self.embeddings):
                self.embeddings.pop(idx)
                self.metadata.pop(idx)
                removed += 1
        
        self.total_entries -= removed
        self.updated_at = datetime.now().isoformat()
        
        return removed
    
    def get_entry(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get entry metadata by index.
        
        Args:
            index: Entry index
        
        Returns:
            Metadata dict or None if not found
        """
        if 0 <= index < len(self.metadata):
            return self.metadata[index].copy()
        return None
    
    def get_embedding(self, index: int) -> Optional[List[float]]:
        """
        Get embedding by index.
        
        Args:
            index: Entry index
        
        Returns:
            Embedding vector or None if not found
        """
        if 0 <= index < len(self.embeddings):
            return self.embeddings[index].copy()
        return None
    
    def clear(self) -> None:
        """Clear all entries from the index."""
        self.embeddings = []
        self.metadata = []
        self.total_entries = 0
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "embeddings": self.embeddings,
            "metadata": self.metadata,
            "dimension": self.dimension,
            "total_entries": self.total_entries,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "index_file": self.index_file,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryIndex":
        """
        Create index from dictionary.
        
        Args:
            data: Dictionary with index data
        
        Returns:
            MemoryIndex instance
        """
        index = cls()
        index.embeddings = data.get("embeddings", [])
        index.metadata = data.get("metadata", [])
        index.dimension = data.get("dimension", 384)
        index.total_entries = data.get("total_entries", 0)
        index.created_at = data.get("created_at", datetime.now().isoformat())
        index.updated_at = data.get("updated_at", index.created_at)
        index.index_file = data.get("index_file", "memory_index.pkl")
        
        return index
    
    def get_stats(self) -> dict:
        """
        Get index statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_entries": self.total_entries,
            "dimension": self.dimension,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "memory_size_mb": (
                len(self.embeddings) *
                len(self.embeddings[0]) if self.embeddings else 0
            ) * 8 / 1024 / 1024,  # Approximate MB
        }
    
    def __len__(self) -> int:
        """Return number of entries."""
        return self.total_entries
    
    def __str__(self) -> str:
        """String representation for debugging."""
        stats = self.get_stats()
        return (
            f"MemoryIndex(entries={stats['total_entries']}, "
            f"dimension={stats['dimension']}, "
            f"size={stats['memory_size_mb']:.2f}MB)"
        )
