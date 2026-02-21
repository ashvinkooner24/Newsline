"""
News Aggregation Platform — FastAPI Backend
==========================================

Run with:
    uvicorn main:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
OpenAPI schema:   http://localhost:8000/openapi.json
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.articles import router as articles_router
from api.topics import router as topics_router

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="News Aggregation Platform API",
    description=(
        "REST API for an MVP news aggregation platform. "
        "Articles are scraped, semantically embedded, and clustered into topics. "
        "Each topic exposes a RAG-generated summary, per-segment political bias, "
        "factual accuracy scores, and source citations."
    ),
    version="0.1.0",
    contact={"name": "HackLDN Team"},
)

# ---------------------------------------------------------------------------
# CORS (allow requests from the Vite frontend in development)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default
        "http://localhost:3000",   # CRA / alternative
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(articles_router, prefix="/api/v1")
app.include_router(topics_router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Health & root
# ---------------------------------------------------------------------------


@app.get("/", tags=["Health"], summary="Root ping")
def root():
    return {"status": "ok", "service": "news-aggregation-api", "version": "0.1.0"}


@app.get("/api/v1/health", tags=["Health"], summary="Health check")
def health():
    """Returns liveness status and a count of loaded mock objects."""
    from data.mock_data import ALL_ARTICLES, ALL_TOPICS

    return {
        "status": "ok",
        "articles_loaded": len(ALL_ARTICLES),
        "topics_loaded": len(ALL_TOPICS),
    }
