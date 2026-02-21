from typing import List, Optional
from pydantic import BaseModel

class NewsProvider(BaseModel):
    name: str
    bias_score: float  # -1 (left) to 1 (right)
    trust_score: float  # 0 (low) to 1 (high)

class User(BaseModel):
    username: str
    email: str

class Comment(BaseModel):
    text: str
    like_count: int = 0
    dislike_count: int = 0
    parent: Optional[int] = None  # comment id
    user: Optional[User] = None

class Segment(BaseModel):
    text: str
    sources: List[NewsProvider]
    avg_bias: float
    avg_truth: float
    article_count: int
    notes: Optional[str] = None
    comments: List[Comment] = []

class Story(BaseModel):
    heading: str
    political_bias: float
    factual_accuracy: float
    sources: List[NewsProvider]
    segments: List[Segment]

class StoryWrapper(BaseModel):
    story: Story
    comments: List[Comment]

# Skeleton for LLM chunking/embedding

def get_segments(raw_articles: List[str], providers: List[NewsProvider]) -> List[Segment]:
    """Stub: Use LLM to chunk and embed articles. Returns segments."""
    pass
