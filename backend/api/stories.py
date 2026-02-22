from __future__ import annotations

from fastapi import APIRouter, HTTPException
from ..models import TopicSummary, UserProfile
from ..data.mockData import mock_users, get_topics as _get_topics_with_fallback

router = APIRouter()


# ── Helper ────────────────────────────────────────────────────────────────────

def _all_topics() -> list[TopicSummary]:
    return _get_topics_with_fallback()


# ── Stories ───────────────────────────────────────────────────────────────────

@router.get("/stories", response_model=list[TopicSummary])
def get_stories():
    return _all_topics()


@router.get("/stories/{slug}", response_model=TopicSummary)
def get_story(slug: str):
    for topic in _all_topics():
        if topic.slug == slug:
            return topic
    raise HTTPException(status_code=404, detail=f"Story '{slug}' not found")


# ── Pipeline status ───────────────────────────────────────────────────────────

@router.get("/pipeline/status")
def get_pipeline_status():
    """
    Useful for the frontend to poll while the ML pipeline is loading.
    Returns: {"running": bool, "done": bool, "error": str | None}
    """
    try:
        from ..scoring.pipeline import pipeline_status
        return pipeline_status()
    except Exception as exc:
        return {"running": False, "done": False, "error": str(exc)}


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserProfile])
def get_users():
    return mock_users


@router.get("/users/{user_id}", response_model=UserProfile)
def get_user(user_id: str):
    for user in mock_users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
