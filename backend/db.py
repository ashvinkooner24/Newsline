"""
backend/db.py

Centralised MongoDB connection.

All other modules should import from here instead of creating their own
MongoClient instances or hard-coding connection strings.

Usage:
    from backend.db import get_db, get_collection

    db = get_db()                          # → news_db  (Database)
    stories = get_collection("stories")    # → news_db.stories  (Collection)
"""

import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

# Load .env from project root (two levels up from this file)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGO_URI: str = os.getenv(
    "MONGO_URI",
    "mongodb+srv://ashvinkooner24_db_user:akB6uPnlxpogzfnu@news.nsqauzb.mongodb.net/?appName=News",
)
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "news_db")

# ---------------------------------------------------------------------------
# Singleton client – created lazily on first access
# ---------------------------------------------------------------------------
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Return (and lazily create) the singleton MongoClient."""
    global _client
    # If MongoDB is disabled via env, fail fast to avoid slow SSL handshakes.
    if os.getenv("MONGO_DISABLED", "true").lower() in ("1", "true", "yes"):
        raise RuntimeError("MongoDB usage disabled via MONGO_DISABLED env var")
    if _client is None:
        # Allow opting into relaxed TLS for local troubleshooting via env var.
        allow_invalid = os.getenv("MONGO_TLS_ALLOW_INVALID", "false").lower() in ("1", "true", "yes")
        client_kwargs = {"serverSelectionTimeoutMS": 5000}
        if allow_invalid:
            client_kwargs["tlsAllowInvalidCertificates"] = True
        else:
            client_kwargs["tlsCAFile"] = certifi.where()

        _client = MongoClient(MONGO_URI, **client_kwargs)
        print(f"[db] Connected to MongoDB cluster (db={MONGO_DB_NAME}) (tls_allow_invalid={allow_invalid})")
    return _client


def get_db() -> Database:
    """Return the application database."""
    return get_client()[MONGO_DB_NAME]


def get_collection(name: str) -> Collection:
    """Shortcut: return a collection by name from the application database."""
    return get_db()[name]


# ---------------------------------------------------------------------------
# Convenience accessors for the main collections
# ---------------------------------------------------------------------------


def articles_collection() -> Collection:
    return get_collection("articles")


def stories_collection() -> Collection:
    return get_collection("stories")


def users_collection() -> Collection:
    return get_collection("users")


def comments_collection() -> Collection:
    return get_collection("comments")


# ---------------------------------------------------------------------------
# Lifecycle helpers (called from FastAPI lifespan)
# ---------------------------------------------------------------------------


def ping() -> bool:
    """Quick health-check; returns True if the cluster responds.
    On SSL failure (common on macOS), retries with relaxed TLS settings."""
    global _client
    # Short-circuit when MongoDB is explicitly disabled to avoid connection attempts
    if os.getenv("MONGO_DISABLED", "true").lower() in ("1", "true", "yes"):
        print("[db] MONGO_DISABLED set — skipping MongoDB ping")
        return False

    try:
        get_client().admin.command("ping")
        return True
    except Exception as exc:
        if "SSL" in str(exc) or "TLS" in str(exc):
            print(f"[db] SSL error — retrying with tlsAllowInvalidCertificates…")
            try:
                _client = MongoClient(
                    MONGO_URI,
                    tlsAllowInvalidCertificates=True,
                    serverSelectionTimeoutMS=5000,
                )
                _client.admin.command("ping")
                print(f"[db] Reconnected with relaxed TLS ✓")
                return True
            except Exception as exc2:
                print(f"[db] Ping still failed: {exc2}")
                return False
        print(f"[db] Ping failed: {exc}")
        return False


def close() -> None:
    """Close the MongoClient (call on app shutdown)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        print("[db] MongoDB connection closed")
