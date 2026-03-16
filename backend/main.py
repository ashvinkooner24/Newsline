
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from .models import StoryWrapper, Story, Segment, NewsProvider, User, Comment
from .api.stories import router as stories_router
from .db import ping as db_ping, close as db_close


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──
    if db_ping():
        print("[main] MongoDB connection verified ✓")
    else:
        print("[main] ⚠ MongoDB is unreachable — some endpoints may fail")
    yield
    # ── shutdown ──
    db_close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stories_router)
