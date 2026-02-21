from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PoliticalBiasLabel(str, Enum):
    """Human-readable label derived from a numeric bias score."""
    FAR_LEFT = "far-left"
    LEFT = "left"
    CENTER_LEFT = "center-left"
    CENTER = "center"
    CENTER_RIGHT = "center-right"
    RIGHT = "right"
    FAR_RIGHT = "far-right"


def bias_score_to_label(score: float) -> PoliticalBiasLabel:
    """Convert a numeric bias score [-1, 1] to a qualitative label."""
    if score <= -0.7:
        return PoliticalBiasLabel.FAR_LEFT
    elif score <= -0.35:
        return PoliticalBiasLabel.LEFT
    elif score <= -0.1:
        return PoliticalBiasLabel.CENTER_LEFT
    elif score <= 0.1:
        return PoliticalBiasLabel.CENTER
    elif score <= 0.35:
        return PoliticalBiasLabel.CENTER_RIGHT
    elif score <= 0.7:
        return PoliticalBiasLabel.RIGHT
    else:
        return PoliticalBiasLabel.FAR_RIGHT


class SourceReference(BaseModel):
    """A single news source that contributed to an article or segment."""

    name: str = Field(..., description="Publication or outlet name, e.g. 'Reuters'")
    url: Optional[str] = Field(None, description="Canonical article URL")
    published_at: Optional[str] = Field(
        None, description="ISO-8601 publication timestamp"
    )
    political_bias_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Source-level political bias score: -1 = far-left, 0 = center, 1 = far-right",
    )
    political_bias_label: PoliticalBiasLabel = Field(
        ..., description="Human-readable bias label derived from score"
    )
    credibility_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Source authority / fact-checking credibility (0–1)",
    )

    @classmethod
    def create(
        cls,
        name: str,
        political_bias_score: float,
        credibility_score: float,
        url: Optional[str] = None,
        published_at: Optional[str] = None,
    ) -> "SourceReference":
        return cls(
            name=name,
            url=url,
            published_at=published_at,
            political_bias_score=political_bias_score,
            political_bias_label=bias_score_to_label(political_bias_score),
            credibility_score=credibility_score,
        )


class Segment(BaseModel):
    """
    A single paragraph-level unit of an aggregated article.

    Segments are derived from clustering semantically similar chunks across
    source articles. Each segment synthesises a single facet of the story.
    """

    segment_id: str = Field(
        ..., description="Unique identifier for this segment within the article"
    )
    text: str = Field(
        ..., description="Synthesised paragraph text for this segment"
    )

    # Cross-article provenance
    sources: list[SourceReference] = Field(
        ...,
        description="Source articles that contributed content to this segment",
    )
    num_articles: int = Field(
        ...,
        ge=1,
        description="Number of distinct source articles that mention this facet",
    )

    # Aggregate signals computed across contributing sources
    avg_political_bias_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Mean political bias score across contributing sources",
    )
    avg_political_bias_label: PoliticalBiasLabel = Field(
        ..., description="Human-readable label for the average bias"
    )
    truth_value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Estimated factual accuracy of this segment (0–1). "
            "Derived from source credibility, cross-article consensus, "
            "and fact-check signals."
        ),
    )

    additional_notes: Optional[str] = Field(
        None,
        description=(
            "Analyst or model-generated notes: caveats, missing context, "
            "contradictions between sources, or confidence qualifiers."
        ),
    )


class Article(BaseModel):
    """
    A fully aggregated, topic-level article produced by the platform.

    This is the primary output object: a single coherent narrative built from
    multiple source articles, annotated with bias and credibility metadata.
    """

    article_id: str = Field(..., description="Unique article identifier (UUID)")
    heading: str = Field(..., description="Synthesised headline for the aggregated article")
    topic_id: str = Field(..., description="ID of the parent topic this article belongs to")

    # Top-level aggregate signals
    political_bias_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Aggregate political bias across all contributing sources",
    )
    political_bias_label: PoliticalBiasLabel = Field(
        ..., description="Human-readable label for the aggregate bias"
    )
    factual_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Overall factual accuracy score (0–1) for the article. "
            "Weighted average of segment truth values."
        ),
    )

    # All sources that contributed to this article
    sources: list[SourceReference] = Field(
        ...,
        description="Deduplicated list of every source that contributed to this article",
    )

    # Paragraph-level breakdown
    segments: list[Segment] = Field(
        ...,
        description="Ordered list of segments forming the body of the article",
    )

    # Optional metadata
    created_at: Optional[str] = Field(
        None, description="ISO-8601 timestamp when this aggregated article was generated"
    )
    cover_image_url: Optional[str] = Field(None)
    tags: list[str] = Field(default_factory=list)
