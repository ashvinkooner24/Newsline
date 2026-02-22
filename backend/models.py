"""
Pydantic models for The Newsline backend.

Naming: all fields use **snake_case**.  The frontend (TypeScript) mirrors these
in camelCase; the mapping lives in ``frontend/src/api/newsApi.ts``.

Hierarchy
---------
TopicSummary          – one consolidated story (top-level API object)
 ├─ SummarySection    – thematic section produced by gemini_article_aggregator
 │   ├─ Citation      – reference back to a source article
 │   └─ SectionStats  – per-section bias / credibility / agreement scores
 ├─ Article           – one article from a single news source
 │   ├─ NewsSource    – the outlet (reputation + bias lean)
 │   ├─ ToneScore     – emotional vs logical ratio (sentiment_scoring)
 │   └─ FactCheck     – verification + missing-context (agreement_scoring)
 ├─ BiasAnalysis      – aggregate bias across all sources
 ├─ CredibilityAssessment – composite credibility (credibility_scoring)
 ├─ Comment / CommunityNote
 └─ Rating
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


# ── Source / Provider ────────────────────────────────────────────────────────

class NewsSource(BaseModel):
    """A news outlet with bias and credibility metadata."""
    id: str
    name: str
    url: str = "#"
    credibility_score: float          # 0–100 (from credibility_scoring)
    bias_lean: str                    # far-left | left | center-left | center | center-right | right | far-right
    country: str = "Unknown"


# ── Article-level models ─────────────────────────────────────────────────────

class ToneScore(BaseModel):
    """Emotional vs logical content split (from sentiment_scoring)."""
    emotional: int
    logical: int


class FactCheck(BaseModel):
    """
    Fact-check assessment for an individual article.
    ``missing_context`` comes from agreement_scoring's missing-context detection.
    """
    verdict: str                      # verified | mostly-true | mixed | misleading | unverified
    details: str
    missing_context: List[str] = []


class Article(BaseModel):
    """A single article from one news source, enriched with scoring data."""
    id: str
    title: str
    url: str = "#"
    source: NewsSource
    published_at: str
    excerpt: str
    tone: Optional[str] = None        # emotional | balanced | analytical | sensational
    tone_score: Optional[ToneScore] = None
    fact_check: Optional[FactCheck] = None


# ── Section-level models (Gemini aggregator output) ──────────────────────────

class Citation(BaseModel):
    """A reference from a summary section back to a specific source article."""
    article_id: str
    text: str
    bias_level: Optional[str] = None  # left | right | neutral


class SectionStats(BaseModel):
    """
    Per-section scoring.
    ``credibility_score`` is derived from the cited sources' credibility.
    ``agreement`` comes from agreement_scoring across the cited articles.
    """
    bias_lean: str
    lean_score: float
    credibility_score: float
    source_count: int
    agreement: float


class SummarySection(BaseModel):
    """One thematic section of a consolidated story (from gemini_article_aggregator)."""
    heading: str
    content: str
    citations: List[Citation] = []
    stats: Optional[SectionStats] = None


# ── Story-level aggregates ───────────────────────────────────────────────────

class BiasAnalysis(BaseModel):
    """Aggregate bias analysis for a story, computed from its source leanings."""
    overall_lean: str
    lean_score: float
    left_source_count: int = 0
    center_source_count: int = 0
    right_source_count: int = 0


class CredibilityAssessment(BaseModel):
    """
    Composite credibility for a story.
    Formula: 40 % source reputation · 30 % objectivity · 30 % agreement
    with penalties for contradictions / missing context (credibility_scoring).
    """
    score: float
    article_count: int
    avg_source_credibility: float
    source_agreement: float
    label: str                        # High | Medium | Low | Uncertain


# ── Community / engagement ───────────────────────────────────────────────────

class Comment(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_reputation: int = 50
    text: str
    created_at: str
    likes: int = 0
    dislikes: int = 0
    replies: List[Comment] = []


class CommunityNote(BaseModel):
    id: str
    user_id: str
    user_name: str
    text: str
    helpful_count: int = 0
    unhelpful_count: int = 0
    created_at: str


class Rating(BaseModel):
    accuracy: float
    fairness: float
    completeness: float
    total_ratings: int


# ── Top-level API object ─────────────────────────────────────────────────────

class TopicSummary(BaseModel):
    """
    Top-level object served by ``GET /stories``.

    Represents one consolidated story built from multiple article sources,
    summarised by gemini_article_aggregator and scored for bias, credibility,
    and source agreement by the scoring pipeline.
    """
    id: str
    topic: str
    slug: str
    headline: str
    summary: str
    sections: List[SummarySection]
    articles: List[Article]
    bias_analysis: BiasAnalysis
    credibility: CredibilityAssessment
    updated_at: str
    category: str = "General"
    country: str = "Global"
    subtopic: Optional[str] = None
    is_featured: bool = False
    is_breaking: bool = False
    rating: Optional[Rating] = None
    comments: List[Comment] = []
    community_notes: List[CommunityNote] = []


# ── User / Source profiles ───────────────────────────────────────────────────

class UserProfile(BaseModel):
    id: str
    name: str
    joined_at: str
    articles_read: int = 0
    comments_count: int = 0
    bias_lean: str = "center"
    lean_score: float = 0
    reputation: int = 50
    is_public: bool = True


class SourceProfile(BaseModel):
    source: NewsSource
    total_articles: int
    avg_credibility: float
    bias_history: List[dict] = []
    top_topics: List[str] = []
