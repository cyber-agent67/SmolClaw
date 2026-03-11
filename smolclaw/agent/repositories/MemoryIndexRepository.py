#!/usr/bin/env python3
"""MemoryIndexRepository — persistence for memory index.

Saves and loads the memory index to/from disk using pickle.
Enables fast startup by avoiding re-embedding all memories.
"""

import pickle
import os
from typing import Optional
from smolclaw.agent.entities.MemoryIndex import MemoryIndex


class MemoryIndexRepository:
    """Persistence layer for memory index.
    
    Storage Format: Pickle binary file
    Location: Configurable (default: memory_index.pkl)
    Size: ~1MB per 1000 memories (384-dim embeddings)
    
    Usage:
        # Save index
        MemoryIndexRepository.save(index, "memory_index.pkl")
        
        # Load index
        index = MemoryIndexRepository.load("memory_index.pkl")
        if index is None:
            # Index doesn't exist, create new one
            index = MemoryIndex()
    """
    
    @staticmethod
    def save(
        index: MemoryIndex,
        file_path: str = "memory_index.pkl"
    ) -> bool:
        """
        Save index to disk.
        
        Args:
            index: MemoryIndex to save
            file_path: Path to save file
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # Serialize and save
            data = index.to_dict()
            
            with open(file_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            print(f"✓ Saved memory index: {index.total_entries} entries to {file_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to save memory index: {e}")
            return False
    
    @staticmethod
    def load(file_path: str = "memory_index.pkl") -> Optional[MemoryIndex]:
        """
        Load index from disk.
        
        Args:
            file_path: Path to load file from
        
        Returns:
            MemoryIndex if loaded successfully, None otherwise
        """
        if not os.path.exists(file_path):
            print(f"ℹ Memory index not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            index = MemoryIndex.from_dict(data)
            
            print(f"✓ Loaded memory index: {index.total_entries} entries from {file_path}")
            return index
            
        except Exception as e:
            print(f"✗ Failed to load memory index: {e}")
            return None
    
    @staticmethod
    def exists(file_path: str = "memory_index.pkl") -> bool:
        """
        Check if index file exists.
        
        Args:
            file_path: Path to check
        
        Returns:
            True if exists, False otherwise
        """
        return os.path.exists(file_path)
    
    @staticmethod
    def delete(file_path: str = "memory_index.pkl") -> bool:
        """
        Delete index file.
        
        Args:
            file_path: Path to delete
        
        Returns:
            True if deleted successfully, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            print(f"✓ Deleted memory index: {file_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to delete memory index: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str = "memory_index.pkl") -> int:
        """
        Get index file size in bytes.
        
        Args:
            file_path: Path to check
        
        Returns:
            File size in bytes, or 0 if not found
        """
        if not os.path.exists(file_path):
            return 0
        
        return os.path.getsize(file_path)
    
    @staticmethod
    def get_file_size_human(file_path: str = "memory_index.pkl") -> str:
        """
        Get index file size in human-readable format.
        
        Args:
            file_path: Path to check
        
        Returns:
            Human-readable size string (e.g., "1.5 MB")
        """
        size_bytes = MemoryIndexRepository.get_file_size(file_path)
        
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
