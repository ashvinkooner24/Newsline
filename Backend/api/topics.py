from fastapi import APIRouter, HTTPException, Query
from models.topic import Topic
from data.mock_data import ALL_TOPICS, TOPICS_BY_ID

router = APIRouter(prefix="/topics", tags=["Topics"])


@router.get("/", response_model=list[Topic], summary="List all topics")
def list_topics(
    tag: str | None = Query(None, description="Filter by tag (case-insensitive)"),
    min_credibility: float = Query(0.0, ge=0.0, le=1.0, description="Minimum credibility score"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Return a paginated list of all topics with their embedded articles."""
    topics = list(ALL_TOPICS)

    if tag:
        tag_lower = tag.lower()
        topics = [t for t in topics if any(tag_lower in tg.lower() for tg in t.tags)]

    if min_credibility > 0.0:
        topics = [t for t in topics if t.credibility_score >= min_credibility]

    return topics[offset : offset + limit]


@router.get("/{topic_id}", response_model=Topic, summary="Get a single topic by ID")
def get_topic(topic_id: str):
    """Fetch a fully populated topic including RAG summary, citations, and all articles."""
    topic = TOPICS_BY_ID.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found.")
    return topic


@router.get("/{topic_id}/summary", summary="Get only the RAG summary for a topic")
def get_topic_summary(topic_id: str):
    """Return the topic's RAG summary and citation mapping without full article bodies."""
    topic = TOPICS_BY_ID.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found.")
    return {
        "topic_id": topic.topic_id,
        "name": topic.name,
        "rag_summary": topic.rag_summary,
        "citation_mapping": topic.citation_mapping,
        "aggregate_political_bias_score": topic.aggregate_political_bias_score,
        "aggregate_political_bias_label": topic.aggregate_political_bias_label,
        "credibility_score": topic.credibility_score,
    }


@router.get("/{topic_id}/articles", summary="List articles belonging to a topic")
def get_topic_articles(topic_id: str):
    """Return all aggregated articles within a given topic."""
    topic = TOPICS_BY_ID.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found.")
    return topic.articles
