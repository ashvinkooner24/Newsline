from typing import List, Optional
from pydantic import BaseModel

class NewsProvider(BaseModel):
    name: str
    bias_score: float  # -1 (left) to 1 (right)
    trust_score: float  # 0 (low) to 1 (high)

class User(BaseModel):
    username: str
    email: str
    reputation: int = 50

class Comment(BaseModel):
    text: str
    like_count: int = 0
    dislike_count: int = 0
    parent: Optional[int] = None  # comment id
    user: Optional[User] = None

class Citation(BaseModel):
    source: str
    article_id: str
    quote: str
    bias_level: str = "neutral"

class ContradictionReport(BaseModel):
    wrong_article: str
    wrong_claim: str
    wrong_source: str = ""
    correct_article: str
    correct_claim: str
    correct_source: str = ""

class ArticleMeta(BaseModel):
    id: str
    title: str
    url: str = "#"
    source: str = "Unknown"
    published_at: Optional[str] = None
    excerpt: str = ""

class Segment(BaseModel):
    heading: str = ""
    text: str
    sources: List[NewsProvider]
    citations: List[Citation] = []
    avg_bias: float
    avg_truth: float
    avg_agreement: float = 0.5
    article_count: int
    notes: Optional[str] = None
    comments: List[Comment] = []

class Story(BaseModel):
    heading: str
    slug: str = ""
    summary: str = ""
    political_bias: float
    factual_accuracy: float
    source_agreement: float = 0.5
    sources: List[NewsProvider]
    segments: List[Segment]
    articles: List[ArticleMeta] = []
    category: str = "General"
    updated_at: str = ""
    contradiction_reports: List[ContradictionReport] = []
    missing_context: dict = {}

class StoryWrapper(BaseModel):
    story: Story
    comments: List[Comment]

# Skeleton for LLM chunking/embedding

def get_segments(raw_articles: List[str], providers: List[NewsProvider]) -> List[Segment]:
    """Stub: Use LLM to chunk and embed articles. Returns segments."""
    return []
