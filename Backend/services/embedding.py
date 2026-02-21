"""
Embedding Service (stub)

Production implementation would:
  1. Accept raw article text chunks
  2. Call a sentence-transformer model (e.g. all-mpnet-base-v2) or a
     hosted embedding API (OpenAI text-embedding-3-large, Cohere embed-v3)
  3. Store vectors in a vector database (Pinecone, Weaviate, pgvector, Qdrant)
  4. Return chunk IDs and their embedding vectors

Install (when implementing):
    pip install sentence-transformers torch
    pip install openai  # if using OpenAI embeddings
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def embed_text(text: str) -> list[float]:
    """
    Return a semantic embedding vector for the given text.

    STUB: returns a deterministic pseudo-vector derived from the text hash.
    Replace with a real embedding model call in production.
    """
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
    # Produce a 384-dimensional pseudo-vector (same dim as all-MiniLM-L6-v2)
    pseudo = [(seed >> (i % 64)) & 0xFF for i in range(384)]
    norm = sum(x**2 for x in pseudo) ** 0.5
    return [x / norm for x in pseudo]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning a list of vectors."""
    return [embed_text(t) for t in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x**2 for x in a) ** 0.5
    mag_b = sum(x**2 for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def find_nearest_topic_centroid(
    chunk_embedding: list[float],
    topic_centroids: dict[str, list[float]],
) -> tuple[str, float]:
    """
    Return the (topic_id, similarity_score) of the nearest topic centroid.

    STUB: in production this would query the vector DB for the nearest centroid.
    """
    best_id, best_score = "", -1.0
    for topic_id, centroid in topic_centroids.items():
        score = cosine_similarity(chunk_embedding, centroid)
        if score > best_score:
            best_id, best_score = topic_id, score
    return best_id, best_score
