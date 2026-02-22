from fastapi import APIRouter, HTTPException
from typing import List
from ..models import StoryWrapper
from ..data.mockData import mock_stories
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