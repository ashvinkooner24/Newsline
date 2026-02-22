from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.stories import router as stories_router

app = FastAPI(title="The Newsline API")

# Allow the Vite dev-server (port 8080) and any other origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stories_router)
