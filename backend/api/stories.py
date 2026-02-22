from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from ..models import StoryWrapper, User
from ..data.mockData import mock_stories, mock_users, add_story
from ..utils.slugify import slugify

router = APIRouter()

@router.get("/stories", response_model=List[StoryWrapper])
def get_stories():
    return mock_stories

@router.get("/stories/{slug}", response_model=StoryWrapper)
def get_story(slug: str):
    for story in mock_stories:
        if slugify(story.story.heading) == slug:
            return story
    raise HTTPException(status_code=404, detail="Story not found")


class IngestRequest(BaseModel):
    articles_dir: str                        # absolute or relative path to folder of .txt files
    credibility_scores: dict = {}            # optional {article_id: float}
    provider_trust_map: dict = {}            # optional {source_name: float}


@router.post("/stories/ingest", response_model=StoryWrapper)
def ingest_story(req: IngestRequest):
    """
    Run the full pipeline for a folder of .txt articles:
      1. Load articles from articles_dir
      2. Call Gemini to aggregate them
      3. Convert to StoryWrapper
      4. Persist to stories.json and add to the live mock_stories list
    """
    try:
        from ..scoring.gemini_article_aggregator import (
            load_api_key, load_articles, build_prompt, call_gemini, gemini_to_storywrapper
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Import error: {e}")

    try:
        api_key = load_api_key()
        articles = load_articles(req.articles_dir)
        prompt = build_prompt(articles)
        gemini_result = call_gemini(api_key, prompt)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    story_dict = gemini_to_storywrapper(
        gemini_result,
        credibility_scores=req.credibility_scores,
        provider_trust_map=req.provider_trust_map,
    )
    wrapper = StoryWrapper(**story_dict)
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