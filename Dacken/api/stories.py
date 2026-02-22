from fastapi import APIRouter, HTTPException
from typing import List
from ..models import StoryWrapper, User
from ..data.mockData import mock_stories, mock_users
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


@router.get("/users", response_model=List[User])
def get_users():
    return mock_users

@router.get("/user/{username}", response_model=User)
def get_user(username: str):
    for user in mock_users:
        if user.username == username:
            return user
    raise HTTPException(status_code=404, detail="User not found")