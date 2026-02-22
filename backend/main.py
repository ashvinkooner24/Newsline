
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from .models import StoryWrapper, Story, Segment, NewsProvider, User, Comment
from .api.stories import router as stories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # nothing to do on startup — pipeline is triggered manually


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stories_router)
