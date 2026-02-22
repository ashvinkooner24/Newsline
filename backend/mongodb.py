import polars as pl
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from datetime import datetime
from tqdm import tqdm

SOURCE = "nytimes"
MONGO_URI = "mongodb+srv://ashvinkooner24_db_user:akB6uPnlxpogzfnu@news.nsqauzb.mongodb.net/?appName=News"
INPUT_DF = f"scraping/{SOURCE}.csv"

model = SentenceTransformer("all-mpnet-base-v2")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
articles_collection = db["articles"]


# ---------------------------
# Upload articles
# ---------------------------
def upload_articles(csv_path):
    df = pl.read_csv(csv_path)
    df = df.fill_null("")

    for row in tqdm(df.iter_rows(named=True), total=len(df)):
        try:
            full_text = f"{row['title']}\n\n{row['text']}"

            embedding = model.encode(full_text).tolist()

            article_doc = {
                "title": row["title"],
                "text": row["text"],
                "source": SOURCE,
                "url": row.get("url", ""),
                "embedding": embedding,
                "created_at": datetime.utcnow()
            }

            articles_collection.insert_one(article_doc)

        except Exception as e:
            print(f"Error processing article: {e}")

    print("Upload complete.")


if __name__ == "__main__":
    upload_articles(INPUT_DF)