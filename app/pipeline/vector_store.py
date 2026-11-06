import numpy as np
from typing import List, Dict, Any, Tuple

class VectorStore:
    """
    High-performance vector embedding store with cosine similarity indexing.
    Supports in-memory high-throughput testing with Pinecone vector DB compatibility.
    """
    def __init__(self, dimension: int = 64):
        self.dimension = dimension
        self.vectors: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def _pseudo_embed(self, text: str) -> np.ndarray:
        """Deterministic pseudo-embedding for testing without requiring heavy external LLM API keys."""
        np.random.seed(abs(hash(text)) % (2**32))
        vec = np.random.randn(self.dimension)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def upsert(self, doc_id: str, text: str, metadata: Dict[str, Any]) -> None:
        emb = self._pseudo_embed(text)
        self.vectors[doc_id] = emb
        self.metadata[doc_id] = metadata

    def query(self, query_text: str, top_k: int = 3) -> List[Tuple[str, float, Dict[str, Any]]]:
        if not self.vectors:
            return []

        q_vec = self._pseudo_embed(query_text)
        results = []

        for doc_id, vec in self.vectors.items():
            similarity = float(np.dot(q_vec, vec))
            results.append((doc_id, similarity, self.metadata[doc_id]))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
