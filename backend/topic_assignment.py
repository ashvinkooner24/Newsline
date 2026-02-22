from pymongo import MongoClient
from datetime import datetime
import os


MONGO_URI = "mongodb+srv://ashvinkooner24_db_user:akB6uPnlxpogzfnu@news.nsqauzb.mongodb.net/?appName=News"
DB_NAME = "news_db"
COLLECTION_NAME = "articles"
VECTOR_INDEX_NAME = "vector_index"

SIMILARITY_THRESHOLD = 0.88  # tune this (0.85–0.92 typical)
NUM_CANDIDATES = 50
SEARCH_LIMIT = 5

# -----------------------------
# MongoDB Connection
# -----------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
articles = db[COLLECTION_NAME]

# -----------------------------
# Generate new topic id
# -----------------------------
def create_new_topic_id():
    return f"topic_{datetime.utcnow().timestamp()}"

# -----------------------------
# Assign topic for ONE article
# -----------------------------
def assign_topic(article):

    embedding = article["embedding"]

    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": NUM_CANDIDATES,
                "limit": SEARCH_LIMIT
            }
        },
        {
            "$project": {
                "_id": 1,
                "topic_id": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = list(articles.aggregate(pipeline))

    # Remove self-match
    results = [r for r in results if r["_id"] != article["_id"]]

    if results:
        best_match = results[0]
        best_score = best_match["score"]

        if (
            best_score >= SIMILARITY_THRESHOLD
            and best_match.get("topic_id") is not None
        ):
            topic_id = best_match["topic_id"]
        else:
            topic_id = create_new_topic_id()
    else:
        topic_id = create_new_topic_id()

    # Update article
    articles.update_one(
        {"_id": article["_id"]},
        {
            "$set": {
                "topic_id": topic_id,
                "topic_assigned_at": datetime.utcnow()
            }
        }
    )

    return topic_id

# -----------------------------
# Assign topics to all unassigned articles
# -----------------------------
def run_topic_assignment():

    unassigned_articles = list(
        articles.find({"topic_id": {"$exists": False}})
    )

    print(f"Found {len(unassigned_articles)} unassigned articles.")

    for article in unassigned_articles:
        topic_id = assign_topic(article)
        print(f"Article {article['_id']} → {topic_id}")

    print("Topic assignment complete.")


if __name__ == "__main__":
    run_topic_assignment()