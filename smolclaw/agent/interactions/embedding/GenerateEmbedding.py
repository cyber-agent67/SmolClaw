#!/usr/bin/env python3
"""GenerateEmbedding interaction — local embeddings (zero API cost).

Generates embedding vectors for text using sentence-transformers.
No API calls, no token cost, completely free.

Model: all-MiniLM-L6-v2 (384 dimensions, 80MB)
Speed: ~50ms per embedding
Cost: $0.00 (local computation)

Note: sentence-transformers is installed automatically with:
    pip install -e .
"""

from typing import List, Optional
from smolclaw.agent.config.MemoryConfig import MemoryConfig


class _EmbeddingModelSingleton:
    """
    Singleton for local embedding model.
    
    Loaded once, reused for all embeddings.
    Zero API cost — runs locally on CPU.
    
    Model: sentence-transformers/all-MiniLM-L6-v2
    - 384 dimensions
    - ~80MB on disk
    - Fast CPU inference
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
    
    def load(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Load sentence-transformers embedding model.
        
        Args:
            model_name: Model to load (default: all-MiniLM-L6-v2)
        """
        if self._model is not None:
            return
        
        from sentence_transformers import SentenceTransformer
        
        print(f"Loading embedding model: {model_name}...")
        self._model = SentenceTransformer(model_name)
        print("✓ Embedding model loaded (local, zero API cost)")
    
    def encode(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (list of floats)
        """
        if self._model is None:
            self.load()
        
        # Generate embedding with sentence-transformers
        embedding = self._model.encode(
            text,
            normalize_embeddings=True,  # Cosine similarity ready
            show_progress_bar=False,
            convert_to_numpy=False
        )
        
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).
        
        More efficient than individual calls.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if self._model is None:
            self.load()
        
        # Batch encode
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=False
        )
        
        return [emb.tolist() for emb in embeddings]


# Global singleton instance
_singleton = _EmbeddingModelSingleton()


class GenerateEmbedding:
    """Generate embedding for text — sentence-transformers, zero API cost.
    
    Usage:
        # Single text
        embedding = GenerateEmbedding.execute("Find FDA requirements")
        
        # Batch
        embeddings = GenerateEmbedding.execute_batch([
            "Task 1",
            "Task 2"
        ])
    
    Performance:
        - Single: ~50ms
        - Batch (10): ~200ms
        - Cost: $0.00 (local CPU)
    
    Model Info:
        - Name: sentence-transformers/all-MiniLM-L6-v2
        - Dimensions: 384
        - Size: ~80MB
        - Installed automatically with pip install -e .
    """
    
    @staticmethod
    def execute(
        text: str,
        config: MemoryConfig = None
    ) -> List[float]:
        """
        Generate embedding vector for text.
        
        Uses local sentence-transformers model — zero API token cost.
        
        Args:
            text: Text to embed
            config: Optional memory configuration (for model name)
        
        Returns:
            Embedding vector (list of floats)
        """
        if config is None:
            config = MemoryConfig()
        
        if not _singleton.is_loaded:
            _singleton.load(config.embedding_model)
        
        return _singleton.encode(text)
    
    @staticmethod
    def execute_batch(
        texts: List[str],
        config: MemoryConfig = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).
        
        More efficient than individual calls.
        
        Args:
            texts: List of texts to embed
            config: Optional memory configuration
        
        Returns:
            List of embedding vectors
        """
        if config is None:
            config = MemoryConfig()
        
        if not _singleton.is_loaded:
            _singleton.load(config.embedding_model)
        
        return _singleton.encode_batch(texts)
    
    @staticmethod
    def preload_model(config: MemoryConfig = None) -> None:
        """
        Preload embedding model (optional optimization).
        
        Call this at startup to avoid first-call latency.
        
        Args:
            config: Optional memory configuration
        """
        if config is None:
            config = MemoryConfig()
        
        if not _singleton.is_loaded:
            _singleton.load(config.embedding_model)
