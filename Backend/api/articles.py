from fastapi import APIRouter, HTTPException, Query
from models.article import Article
from data.mock_data import ALL_ARTICLES, ARTICLES_BY_ID

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("/", response_model=list[Article], summary="List all aggregated articles")
def list_articles(
    topic_id: str | None = Query(None, description="Filter by topic ID"),
    tag: str | None = Query(None, description="Filter by tag (case-insensitive)"),
    min_credibility: float = Query(0.0, ge=0.0, le=1.0, description="Minimum factual accuracy"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Return a paginated list of aggregated articles with optional filters."""
    articles = list(ALL_ARTICLES)

    if topic_id:
        articles = [a for a in articles if a.topic_id == topic_id]

    if tag:
        tag_lower = tag.lower()
        articles = [a for a in articles if any(tag_lower in t.lower() for t in a.tags)]

    if min_credibility > 0.0:
        articles = [a for a in articles if a.factual_accuracy >= min_credibility]

    return articles[offset : offset + limit]


@router.get("/{article_id}", response_model=Article, summary="Get a single article by ID")
def get_article(article_id: str):
    """Fetch a fully populated aggregated article including all segments and sources."""
    article = ARTICLES_BY_ID.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail=f"Article '{article_id}' not found.")
    return article


@router.get("/{article_id}/segments", summary="Get segments for an article")
def get_article_segments(article_id: str):
    """Return only the segments (paragraph breakdown) of a given article."""
    article = ARTICLES_BY_ID.get(article_id)
    if not article:
        raise HTTPException(status_code=404, detail=f"Article '{article_id}' not found.")
    return article.segments
