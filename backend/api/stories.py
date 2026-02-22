from fastapi import APIRouter, HTTPException
from typing import List

from ..models import TopicSummary, UserProfile
from ..data.mockData import mock_topics, mock_users

router = APIRouter()


# ── Stories (TopicSummary) ───────────────────────────────────────────────────

@router.get("/stories", response_model=List[TopicSummary])
def get_stories():
    """Return all consolidated stories with scoring metadata."""
    return mock_topics


@router.get("/stories/{slug}", response_model=TopicSummary)
def get_story(slug: str):
    """Return a single story by its URL slug."""
    for topic in mock_topics:
        if topic.slug == slug:
            return topic
    raise HTTPException(status_code=404, detail="Story not found")


# ── Users ────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserProfile])
def get_users():
    return mock_users


@router.get("/user/{user_id}", response_model=UserProfile)
def get_user(user_id: str):
    for user in mock_users:
        if user.id == user_id or user.name == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")
