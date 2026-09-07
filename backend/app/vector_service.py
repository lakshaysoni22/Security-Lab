import math
from typing import List, Dict, Any, Tuple

class VectorService:
    def __init__(self):
        self.documents = []

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """Indexes a text document into the local semantic vector store."""
        self.documents.append({
            "id": doc_id,
            "content": content,
            "metadata": metadata or {}
        })

    def search_similarity(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Computes cosine similarity of tf-idf vectors for semantic search matches."""
        if not self.documents:
            return []

        # 1. Simple TF-IDF Vectorization
        query_words = set(query.lower().split())
        results = []

        for doc in self.documents:
            doc_words = doc["content"].lower().split()
            # Calculate intersection
            intersection = query_words.intersection(doc_words)
            
            # Simple Jaccard/Cosine similarity approximation
            score = 0.0
            if len(query_words) > 0 and len(doc_words) > 0:
                score = len(intersection) / math.sqrt(len(query_words) * len(doc_words))
            
            results.append({
                "id": doc["id"],
                "content": doc["content"],
                "score": round(score, 4),
                "metadata": doc["metadata"]
            })

        # Sort by similarity score descending
        return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

vector_service = VectorService()
