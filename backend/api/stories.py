from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from ..models import StoryWrapper, User
from ..data.mockData import mock_stories, mock_users, add_story
from ..utils.slugify import slugify

router = APIRouter()


def _get_stories() -> list[StoryWrapper]:
    """
    Return stories from the pipeline cache when available,
    falling back to mock_stories (seeded from stories.json on startup).
    """
    try:
        from ..scoring.pipeline import get_cached_stories
        cached = get_cached_stories()
        if cached:
            return [StoryWrapper(**s) if isinstance(s, dict) else s for s in cached]
    except Exception:
        pass
    return mock_stories


@router.get("/pipeline/status")
def pipeline_status():
    """Surface the current state of the background scoring pipeline."""
    try:
        from ..scoring.pipeline import get_pipeline_status
        return get_pipeline_status()
    except Exception as exc:
        return {"state": "unavailable", "error": str(exc)}


@router.get("/stories", response_model=List[StoryWrapper])
def get_stories():
    return _get_stories()


@router.get("/stories/{slug}", response_model=StoryWrapper)
def get_story(slug: str):
    for story in _get_stories():
        if slugify(story.story.heading) == slug:
            return story
    raise HTTPException(status_code=404, detail="Story not found")


class IngestRequest(BaseModel):
    articles_dir: str   # absolute or relative path to a folder of .txt files


@router.post("/stories/ingest", response_model=StoryWrapper)
def ingest_story(req: IngestRequest):
    """
    Run the full scoring pipeline (sentiment → agreement → credibility → Gemini)
    for a folder of .txt articles, persist the result, and return it.
    """
    try:
        from ..scoring.pipeline import run_pipeline
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Import error: {e}")

    try:
        results = run_pipeline(req.articles_dir)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    wrapper = StoryWrapper(**results[0])
    add_story(wrapper)
    return wrapper


@router.get("/users", response_model=List[User])
def get_users():
    return mock_users

@router.get("/user/{username}", response_model=User)
def get_user(username: str):
    for user in mock_users:
        if user.username == username:
            return user
    raise HTTPException(status_code=404, detail="User not found")