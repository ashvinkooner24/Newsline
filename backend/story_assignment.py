from datetime import datetime

from .db import articles_collection as _articles_collection

COLLECTION_NAME = "articles"
VECTOR_INDEX_NAME = "vector_index"

SIMILARITY_THRESHOLD = 0.88  # tune this (0.85–0.92 typical)
NUM_CANDIDATES = 50
SEARCH_LIMIT = 5

# -----------------------------
# DB handle
# -----------------------------
articles = _articles_collection()


# -----------------------------
# Generate new story id
# -----------------------------
def create_new_story_id() -> str:
    return f"story_{datetime.utcnow().timestamp()}"


# -----------------------------
# Assign story for ONE article
# -----------------------------
def assign_story(article: dict) -> str:
    embedding = article["embedding"]

    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": NUM_CANDIDATES,
                "limit": SEARCH_LIMIT,
            }
        },
        {
            "$project": {
                "_id": 1,
                "story_id": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    results = list(articles.aggregate(pipeline))

    # Remove self-match
    results = [r for r in results if r["_id"] != article["_id"]]

    if results:
        best_match = results[0]
        best_score = best_match["score"]

        if (
            best_score >= SIMILARITY_THRESHOLD
            and best_match.get("story_id") is not None
        ):
            story_id = best_match["story_id"]
        else:
            story_id = create_new_story_id()
    else:
        story_id = create_new_story_id()

    # Update article
    articles.update_one(
        {"_id": article["_id"]},
        {
            "$set": {
                "story_id": story_id,
                "story_assigned_at": datetime.utcnow(),
            }
        },
    )

    return story_id


# -----------------------------
# Assign stories to all unassigned articles
# -----------------------------
def run_story_assignment() -> None:
    unassigned_articles = list(
        articles.find({"story_id": {"$exists": False}})
    )

    print(f"Found {len(unassigned_articles)} unassigned articles.")

    for article in unassigned_articles:
        story_id = assign_story(article)
        print(f"Article {article['_id']} → {story_id}")

    print("Story assignment complete.")


if __name__ == "__main__":
    run_story_assignment()
