"""
mockData.py

Provides `get_topics()` and `mock_users` for the API.

`get_topics()` returns the pipeline result if available, otherwise falls
back to inline stub topics so the frontend is never left empty.
"""

from __future__ import annotations

from ..models import (
    Article,
    BiasAnalysis,
    Citation,
    CredibilityAssessment,
    NewsSource,
    SectionStats,
    SummarySection,
    TopicSummary,
    UserProfile,
)

# ── User stubs ────────────────────────────────────────────────────────────────

mock_users: list[UserProfile] = [
    UserProfile(id="u1", name="DataDrivenReader", joined_at="2025-06-15",
                articles_read=342, comments_count=28, bias_lean="center",
                lean_score=-3, reputation=87, is_public=True),
    UserProfile(id="u2", name="SkepticalObserver", joined_at="2025-09-01",
                articles_read=198, comments_count=45, bias_lean="center-left",
                lean_score=-15, reputation=72, is_public=True),
    UserProfile(id="u3", name="MediaAnalyst", joined_at="2025-03-20",
                articles_read=567, comments_count=89, bias_lean="center",
                lean_score=2, reputation=91, is_public=True),
    UserProfile(id="u4", name="NewsJunkie42", joined_at="2025-11-10",
                articles_read=112, comments_count=12, bias_lean="center-right",
                lean_score=18, reputation=65, is_public=False),
    UserProfile(id="u5", name="FactChecker101", joined_at="2025-01-05",
                articles_read=890, comments_count=156, bias_lean="center",
                lean_score=-1, reputation=95, is_public=True),
]

# ── Fallback stubs (used while pipeline is loading or if it fails) ────────────

_GUARDIAN = NewsSource(id="guardian", name="The Guardian",
                       url="https://theguardian.com", credibility_score=82,
                       bias_lean="center-left", country="UK")
_BBC      = NewsSource(id="bbc", name="BBC News",
                       url="https://bbc.co.uk", credibility_score=88,
                       bias_lean="center", country="UK")
_REUTERS  = NewsSource(id="reuters", name="Reuters",
                       url="https://reuters.com", credibility_score=92,
                       bias_lean="center", country="UK")

_fallback_topics: list[TopicSummary] = [
    TopicSummary(
        id="pipeline-loading",
        topic="Loading…",
        slug="pipeline-loading",
        headline="The scoring pipeline is running — results will appear shortly.",
        summary=(
            "The backend is processing articles through the full scoring pipeline "
            "(sentiment, agreement, credibility, Gemini aggregation). "
            "Refresh in a moment to see the real story."
        ),
        sections=[
            SummarySection(
                heading="Pipeline status",
                content=(
                    "Sentiment scoring, cross-article agreement detection, "
                    "credibility computation, and Gemini article aggregation "
                    "are running in the background."
                ),
                citations=[],
                stats=SectionStats(
                    bias_lean="center", lean_score=0,
                    credibility_score=0, source_count=0, agreement=0,
                ),
            )
        ],
        articles=[
            Article(id="loading-1", title="Pipeline running…", url="#",
                    source=_GUARDIAN, published_at="2026-02-22",
                    excerpt="Results will appear once processing completes."),
        ],
        bias_analysis=BiasAnalysis(overall_lean="center", lean_score=0,
                                   left_source_count=0, center_source_count=1,
                                   right_source_count=0),
        credibility=CredibilityAssessment(score=0, article_count=0,
                                          avg_source_credibility=0,
                                          source_agreement=0, label="Uncertain"),
        updated_at="2026-02-22T00:00:00Z",
        category="System",
        country="Global",
        comments=[],
        community_notes=[],
    )
]


# Public alias so any existing code that imports `mock_topics` still works
mock_topics: list[TopicSummary] = _fallback_topics


# ── Dynamic topic getter ──────────────────────────────────────────────────────

def get_topics() -> list[TopicSummary]:
    """
    Return pipeline-produced topics if ready, otherwise fallback stubs.
    """
    try:
        from ..scoring.pipeline import get_topics as _pipeline_topics
        result = _pipeline_topics()
        if result:
            return result
    except Exception as exc:
        print(f"[mockData] Pipeline topics unavailable: {exc}", flush=True)
    return _fallback_topics
