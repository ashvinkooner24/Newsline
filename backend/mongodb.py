from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from datetime import datetime
import numpy as np

# --- Setup ---
MONGO_URI = "mongodb+srv://ashvinkooner24_db_user:akB6uPnlxpogzfnu@news.nsqauzb.mongodb.net/?appName=News"

client = MongoClient(MONGO_URI)
db = client["news_db"]
articles_col = db["articles"]
chunks_col = db["chunks"]

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Chunking Function ---
def chunk_text(text, chunk_size=400):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

# --- Main Insertion Function ---
def insert_article(article_data):
    """
    article_data = {
        "title": "...",
        "body": "...",
        "source": "...",
        "publish_date": datetime(...)
    }
    """

    # Chunk the article
    chunks = chunk_text(article_data["body"])

    # Generate embeddings for chunks
    chunk_embeddings = model.encode(
        chunks,
        normalize_embeddings=True
    )

    # Compute article-level embedding (mean of chunks)
    article_embedding = np.mean(chunk_embeddings, axis=0)

    # Insert article document
    article_doc = {
        "title": article_data["title"],
        "body": article_data["body"],
        "source": article_data["source"],
        "publish_date": article_data["publish_date"],
        "article_embedding": article_embedding.tolist(),
        "created_at": datetime.utcnow()
    }

    article_result = articles_col.insert_one(article_doc)
    article_id = article_result.inserted_id

    # Insert chunk documents
    chunk_docs = []
    for chunk_text, embedding in zip(chunks, chunk_embeddings):
        chunk_docs.append({
            "article_id": article_id,
            "text": chunk_text,
            "embedding": embedding.tolist()
        })

    if chunk_docs:
        chunks_col.insert_many(chunk_docs)
