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

import json
import os
import sqlite3
import threading
import uuid
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Any

# Load .env from project root (two levels up from this file)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGO_URI: str = os.getenv(
    "MONGO_URI",
    "mongodb+srv://ashvinkooner24_db_user:akB6uPnlxpogzfnu@news.nsqauzb.mongodb.net/?appName=News",
)
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "news_db")
SQLITE_DB_PATH: str = os.getenv(
    "SQLITE_DB_PATH",
    os.path.join(os.path.dirname(__file__), "data", "app.db"),
)

# ---------------------------------------------------------------------------
# Singleton client – created lazily on first access
# ---------------------------------------------------------------------------
_client: MongoClient | None = None
_sqlite_conn: sqlite3.Connection | None = None
_sqlite_lock = threading.Lock()
_backend_mode: str | None = None  # "mongo" | "sqlite"


def _is_truthy(value: str | None, default: str = "false") -> bool:
    return (value or default).lower() in ("1", "true", "yes")


def _mongo_disabled() -> bool:
    return _is_truthy(os.getenv("MONGO_DISABLED"), default="false")


def _init_sqlite() -> sqlite3.Connection:
    """Create sqlite connection + schema if needed."""
    global _sqlite_conn
    if _sqlite_conn is None:
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        _sqlite_conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        _sqlite_conn.execute("PRAGMA journal_mode=WAL;")
        _sqlite_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                collection TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                data TEXT NOT NULL,
                PRIMARY KEY (collection, doc_id)
            )
            """
        )
        _sqlite_conn.commit()
        print(f"[db] SQLite ready at {SQLITE_DB_PATH}")
    return _sqlite_conn


def _select_backend() -> str:
    """Pick and memoize active backend (mongo first, sqlite fallback)."""
    global _backend_mode
    if _backend_mode is not None:
        return _backend_mode

    forced_backend = (os.getenv("DB_BACKEND") or "").strip().lower()
    if forced_backend == "sqlite":
        _init_sqlite()
        _backend_mode = "sqlite"
        print("[db] Using SQLite backend (DB_BACKEND=sqlite)")
        return _backend_mode

    if forced_backend == "mongo" and _mongo_disabled():
        raise RuntimeError("DB_BACKEND=mongo but MongoDB is disabled via MONGO_DISABLED")

    if not _mongo_disabled():
        try:
            get_client().admin.command("ping")
            _backend_mode = "mongo"
            print("[db] Active backend: MongoDB")
            return _backend_mode
        except Exception as exc:
            print(f"[db] MongoDB unavailable, falling back to SQLite: {exc}")

    _init_sqlite()
    _backend_mode = "sqlite"
    print("[db] Active backend: SQLite")
    return _backend_mode


def get_active_backend() -> str:
    """Return the currently selected backend name."""
    return _select_backend()


class SQLiteCollection:
    """Tiny Mongo-like collection adapter over SQLite JSON storage."""

    def __init__(self, conn: sqlite3.Connection, name: str):
        self.conn = conn
        self.name = name

    def _load_docs(self) -> list[dict[str, Any]]:
        with _sqlite_lock:
            rows = self.conn.execute(
                "SELECT data FROM documents WHERE collection = ?",
                (self.name,),
            ).fetchall()
        docs: list[dict[str, Any]] = []
        for (data,) in rows:
            try:
                docs.append(json.loads(data))
            except Exception:
                continue
        return docs

    @staticmethod
    def _matches_filter(doc: dict[str, Any], filt: dict[str, Any] | None) -> bool:
        if not filt:
            return True
        for key, expected in filt.items():
            if isinstance(expected, dict) and "$exists" in expected:
                exists = key in doc
                if exists != bool(expected["$exists"]):
                    return False
            elif doc.get(key) != expected:
                return False
        return True

    @staticmethod
    def _apply_projection(doc: dict[str, Any], projection: dict[str, int] | None) -> dict[str, Any]:
        if not projection:
            return dict(doc)
        out = dict(doc)
        for key, include in projection.items():
            if include == 0 and key in out:
                out.pop(key, None)
        return out

    @staticmethod
    def _ensure_id(doc: dict[str, Any]) -> dict[str, Any]:
        out = dict(doc)
        if "_id" not in out:
            out["_id"] = uuid.uuid4().hex
        return out

    def _upsert_doc(self, doc: dict[str, Any]) -> None:
        doc = self._ensure_id(doc)
        with _sqlite_lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO documents(collection, doc_id, data) VALUES(?, ?, ?)",
                (self.name, str(doc["_id"]), json.dumps(doc, ensure_ascii=False)),
            )
            self.conn.commit()

    def insert_one(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc = self._ensure_id(doc)
        self._upsert_doc(doc)
        return {"inserted_id": doc["_id"]}

    def insert_many(self, docs: list[dict[str, Any]]) -> dict[str, Any]:
        inserted_ids = []
        for doc in docs:
            with_id = self._ensure_id(doc)
            inserted_ids.append(with_id["_id"])
            self._upsert_doc(with_id)
        return {"inserted_ids": inserted_ids}

    def find(self, filt: dict[str, Any] | None = None, projection: dict[str, int] | None = None):
        docs = self._load_docs()
        return [
            self._apply_projection(d, projection)
            for d in docs
            if self._matches_filter(d, filt)
        ]

    def find_one(self, filt: dict[str, Any] | None = None, projection: dict[str, int] | None = None):
        docs = self.find(filt, projection)
        return docs[0] if docs else None

    def delete_many(self, filt: dict[str, Any] | None = None) -> dict[str, Any]:
        docs = self._load_docs()
        keep = [d for d in docs if not self._matches_filter(d, filt)]
        deleted_count = len(docs) - len(keep)
        with _sqlite_lock:
            self.conn.execute("DELETE FROM documents WHERE collection = ?", (self.name,))
            for d in keep:
                d = self._ensure_id(d)
                self.conn.execute(
                    "INSERT OR REPLACE INTO documents(collection, doc_id, data) VALUES(?, ?, ?)",
                    (self.name, str(d["_id"]), json.dumps(d, ensure_ascii=False)),
                )
            self.conn.commit()
        return {"deleted_count": deleted_count}

    def replace_one(self, filt: dict[str, Any], replacement: dict[str, Any], upsert: bool = False) -> dict[str, Any]:
        docs = self._load_docs()
        for d in docs:
            if self._matches_filter(d, filt):
                merged = dict(replacement)
                if "_id" not in merged and "_id" in d:
                    merged["_id"] = d["_id"]
                self._upsert_doc(merged)
                return {"matched_count": 1, "modified_count": 1}
        if upsert:
            merged = dict(filt)
            merged.update(replacement)
            self._upsert_doc(merged)
            return {"matched_count": 0, "modified_count": 0, "upserted": 1}
        return {"matched_count": 0, "modified_count": 0}

    def update_one(self, filt: dict[str, Any], update: dict[str, Any], upsert: bool = False) -> dict[str, Any]:
        docs = self._load_docs()
        for d in docs:
            if self._matches_filter(d, filt):
                if "$set" in update and isinstance(update["$set"], dict):
                    d.update(update["$set"])
                self._upsert_doc(d)
                return {"matched_count": 1, "modified_count": 1}
        if upsert:
            new_doc = dict(filt)
            if "$set" in update and isinstance(update["$set"], dict):
                new_doc.update(update["$set"])
            self._upsert_doc(new_doc)
            return {"matched_count": 0, "modified_count": 0, "upserted": 1}
        return {"matched_count": 0, "modified_count": 0}


def get_client() -> MongoClient:
    """Return (and lazily create) the singleton MongoClient."""
    global _client
    # If MongoDB is disabled via env, fail fast to avoid slow SSL handshakes.
    if _mongo_disabled():
        raise RuntimeError("MongoDB usage disabled via MONGO_DISABLED env var")
    if _client is None:
        # Allow opting into relaxed TLS for local troubleshooting via env var.
        allow_invalid = os.getenv("MONGO_TLS_ALLOW_INVALID", "false").lower() in ("1", "true", "yes")
        client_kwargs: dict[str, Any] = {"serverSelectionTimeoutMS": 5000}
        if allow_invalid:
            client_kwargs["tlsAllowInvalidCertificates"] = True
        else:
            client_kwargs["tlsCAFile"] = certifi.where()

        _client = MongoClient(MONGO_URI, **client_kwargs)
        print(f"[db] MongoClient created (db={MONGO_DB_NAME}) (tls_allow_invalid={allow_invalid})")
    return _client


def get_db() -> Database:
    """Return the application database."""
    if _select_backend() != "mongo":
        raise RuntimeError("Active backend is SQLite; MongoDB Database handle unavailable")
    return get_client()[MONGO_DB_NAME]


def get_collection(name: str) -> Any:
    """Shortcut: return a collection by name from the application database."""
    if _select_backend() == "mongo":
        return get_db()[name]
    return SQLiteCollection(_init_sqlite(), name)


# ---------------------------------------------------------------------------
# Convenience accessors for the main collections
# ---------------------------------------------------------------------------


def articles_collection() -> Any:
    return get_collection("articles")


def stories_collection() -> Any:
    return get_collection("stories")


def users_collection() -> Any:
    return get_collection("users")


def comments_collection() -> Any:
    return get_collection("comments")


# ---------------------------------------------------------------------------
# Lifecycle helpers (called from FastAPI lifespan)
# ---------------------------------------------------------------------------


def ping() -> bool:
    """Quick health-check; returns True if the cluster responds.
    On SSL failure (common on macOS), retries with relaxed TLS settings."""
    global _client
    backend = _select_backend()
    if backend != "mongo":
        print("[db] MongoDB ping skipped (SQLite backend active)")
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
    global _sqlite_conn
    if _sqlite_conn is not None:
        _sqlite_conn.close()
        _sqlite_conn = None
        print("[db] SQLite connection closed")
