
from fastapi import FastAPI
from typing import List
from .models import StoryWrapper, Story, Segment, NewsProvider, User, Comment
from .api.stories import router as stories_router

app = FastAPI()

app.include_router(stories_router, prefix="/api")

