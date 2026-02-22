from pymongo import MongoClient

client = MongoClient(MONGO_URI)
db = client["news_db"]
topics = db["topics"]

SIMILARITY_THRESHOLD = 0.82

def find_best_topic(article_embedding):
    pipeline = [
        {
            "$vectorSearch": {
                "index": "topic_vector_index",  # name of your Atlas vector index
                "path": "centroid_embedding",
                "queryVector": article_embedding,
                "numCandidates": 50,
                "limit": 1
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = list(topics.aggregate(pipeline))
    return results[0] if results else None

best_topic = find_best_topic(article_embedding)

if best_topic and best_topic["score"] > SIMILARITY_THRESHOLD:
    topic_id = best_topic["_id"]
else:
    topic_id = create_new_topic(article_embedding)