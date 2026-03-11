#!/usr/bin/env python3
"""ComputeSimilarity interaction — cosine similarity (pure math, zero cost).

Computes cosine similarity between two embedding vectors.
Pure mathematical operation — no API calls, no token cost.

Formula:
    similarity = (A · B) / (||A|| × ||B||)

Range:
    0.0 = completely dissimilar
    1.0 = identical
    -1.0 = opposite (rare for normalized embeddings)

Speed: <1ms per comparison
Cost: $0.00 (pure Python math)
"""

from typing import List


class ComputeSimilarity:
    """Compute cosine similarity between embeddings.
    
    Pure math — no API calls, no token cost.
    
    Usage:
        similarity = ComputeSimilarity.execute(
            embedding_a,
            embedding_b
        )
        
        if similarity > 0.7:
            print("Highly similar!")
        elif similarity > 0.4:
            print("Moderately similar")
        else:
            print("Not similar")
    
    Performance:
        - Single comparison: <1ms
        - Cost: $0.00
    """
    
    @staticmethod
    def execute(
        embedding_a: List[float],
        embedding_b: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding_a: First embedding vector
            embedding_b: Second embedding vector
        
        Returns:
            Cosine similarity score (0.0 to 1.0 for normalized embeddings)
            
        Example:
            >>> emb_a = [0.1, 0.2, 0.3]
            >>> emb_b = [0.1, 0.2, 0.3]
            >>> ComputeSimilarity.execute(emb_a, emb_b)
            1.0  # Identical
            
            >>> emb_c = [0.3, 0.2, 0.1]
            >>> ComputeSimilarity.execute(emb_a, emb_c)
            0.77  # Similar but not identical
        """
        # Handle edge cases
        if not embedding_a or not embedding_b:
            return 0.0
        
        if len(embedding_a) != len(embedding_b):
            # Different dimensions — can't compare
            return 0.0
        
        # Compute dot product
        dot_product = sum(a * b for a, b in zip(embedding_a, embedding_b))
        
        # Compute magnitudes
        magnitude_a = sum(a * a for a in embedding_a) ** 0.5
        magnitude_b = sum(b * b for b in embedding_b) ** 0.5
        
        # Handle zero magnitudes
        if magnitude_a == 0.0 or magnitude_b == 0.0:
            return 0.0
        
        # Compute cosine similarity
        similarity = dot_product / (magnitude_a * magnitude_b)
        
        # Clamp to valid range (numerical stability)
        similarity = max(-1.0, min(1.0, similarity))
        
        # For normalized embeddings (our case), should be 0.0 to 1.0
        # But we return the raw value for completeness
        return similarity
    
    @staticmethod
    def execute_batch(
        query_embedding: List[float],
        candidate_embeddings: List[List[float]]
    ) -> List[float]:
        """
        Compute similarity between query and multiple candidates.
        
        More efficient than individual calls in a loop.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
        
        Returns:
            List of similarity scores (one per candidate)
        """
        similarities = []
        
        for candidate in candidate_embeddings:
            sim = ComputeSimilarity.execute(query_embedding, candidate)
            similarities.append(sim)
        
        return similarities
    
    @staticmethod
    def find_most_similar(
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        candidate_metadata: List[dict] = None
    ) -> dict:
        """
        Find the most similar candidate to the query.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            candidate_metadata: Optional metadata for each candidate
        
        Returns:
            Dictionary with most similar candidate info
        """
        if not candidate_embeddings:
            return {
                "index": -1,
                "similarity": 0.0,
                "metadata": None
            }
        
        # Compute all similarities
        similarities = ComputeSimilarity.execute_batch(
            query_embedding,
            candidate_embeddings
        )
        
        # Find max
        max_idx = similarities.index(max(similarities))
        max_sim = similarities[max_idx]
        
        result = {
            "index": max_idx,
            "similarity": max_sim,
            "metadata": candidate_metadata[max_idx] if candidate_metadata else None
        }
        
        return result
    
    @staticmethod
    def find_above_threshold(
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        threshold: float = 0.5,
        candidate_metadata: List[dict] = None
    ) -> List[dict]:
        """
        Find all candidates above similarity threshold.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            threshold: Minimum similarity threshold
            candidate_metadata: Optional metadata for each candidate
        
        Returns:
            List of candidates above threshold (sorted by similarity)
        """
        if not candidate_embeddings:
            return []
        
        # Compute all similarities
        similarities = ComputeSimilarity.execute_batch(
            query_embedding,
            candidate_embeddings
        )
        
        # Filter and sort
        results = []
        for i, sim in enumerate(similarities):
            if sim >= threshold:
                results.append({
                    "index": i,
                    "similarity": sim,
                    "metadata": candidate_metadata[i] if candidate_metadata else None
                })
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results
