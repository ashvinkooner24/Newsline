import polars as pl
from sentence_transformers import SentenceTransformer
from datetime import datetime
from tqdm import tqdm

from .db import get_client, articles_collection, MONGO_URI, MONGO_DB_NAME

SOURCE = "nytimes"
INPUT_DF = f"scraping/{SOURCE}.csv"

model = SentenceTransformer("all-mpnet-base-v2")

# Use the centralised connection
articles_col = articles_collection()


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

            articles_col.insert_one(article_doc)

        except Exception as e:
            print(f"Error processing article: {e}")

    print("Upload complete.")


if __name__ == "__main__":
    upload_articles(INPUT_DF)