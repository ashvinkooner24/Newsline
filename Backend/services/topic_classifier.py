"""
Topic Classifier (stub)

Production implementation would:
  1. Maintain a set of topic centroid vectors in the vector DB.
     Centroids are re-computed incrementally as new articles arrive.
  2. For each incoming article chunk, compute cosine similarity against
     all topic centroids.
  3. Assign the chunk to the topic whose centroid has the highest cosine
     similarity, subject to a minimum threshold (e.g. 0.65).
  4. If no topic exceeds the threshold, create a new topic cluster.
  5. Periodically merge topic clusters whose centroids drift close together.

Dependencies (when implementing):
    pip install numpy scikit-learn
    # Vector DB: pinecone-client | qdrant-client | psycopg2 (pgvector)
"""

from __future__ import annotations

from services.embedding import cosine_similarity

# Minimum cosine similarity required to assign a chunk to an existing topic
ASSIGNMENT_THRESHOLD = 0.65


def assign_chunk_to_topic(
    chunk_embedding: list[float],
    topic_centroids: dict[str, list[float]],
) -> str | None:
    """
    Return the topic_id of the best matching topic, or None if no topic
    exceeds the ASSIGNMENT_THRESHOLD (indicating a potential new topic).
    """
    best_id, best_score = None, 0.0
    for topic_id, centroid in topic_centroids.items():
        score = cosine_similarity(chunk_embedding, centroid)
        if score > best_score:
            best_id, best_score = topic_id, score

    if best_score >= ASSIGNMENT_THRESHOLD:
        return best_id
    return None  # Caller should create a new topic cluster


def update_centroid(
    current_centroid: list[float],
    new_embedding: list[float],
    current_count: int,
) -> list[float]:
    """
    Incrementally update a topic centroid with a new article embedding.
    Uses an online mean update: new_centroid = (old * n + new) / (n + 1)
    """
    n = current_count
    return [(c * n + e) / (n + 1) for c, e in zip(current_centroid, new_embedding)]


def should_merge_topics(
    centroid_a: list[float],
    centroid_b: list[float],
    merge_threshold: float = 0.90,
) -> bool:
    """Return True if two topic centroids are similar enough to be merged."""
    return cosine_similarity(centroid_a, centroid_b) >= merge_threshold
