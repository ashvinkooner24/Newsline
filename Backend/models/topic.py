from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from .article import Article, PoliticalBiasLabel


class CitationMapping(BaseModel):
    """Maps a citation token used inside a RAG summary to its source chunk."""

    citation_id: str = Field(..., description="Token used in the summary, e.g. '[1]'")
    article_id: str = Field(..., description="ID of the source article")
    segment_id: str = Field(..., description="ID of the segment within the article")
    source_name: str = Field(..., description="Human-readable source name")
    excerpt: str = Field(..., description="Short quote from the source chunk")
    url: Optional[str] = Field(None)


class Topic(BaseModel):
    """
    A news topic: the top-level container produced by the platform.

    Topics are discovered by clustering article embeddings. Each topic bundles:
      - A RAG-generated prose summary with inline citations
      - One or more aggregated articles (the detailed breakdown)
      - Aggregate political bias and credibility metadata
    """

    topic_id: str = Field(..., description="Unique topic identifier (UUID)")
    name: str = Field(..., description="Short topic label, e.g. 'Federal Reserve Rate Hike'")
    description: str = Field(..., description="One-sentence topic description")

    # RAG summary
    rag_summary: str = Field(
        ...,
        description=(
            "Model-generated prose summary of the topic with inline citation "
            "tokens, e.g. '…the rate was raised by 25 bps [1]…'"
        ),
    )
    citation_mapping: list[CitationMapping] = Field(
        ...,
        description="Ordered list mapping each citation token to its source chunk",
    )

    # Aggregate signals across all articles in the topic
    aggregate_political_bias_score: float = Field(
        ..., ge=-1.0, le=1.0,
        description="Mean political bias score across all contributing sources"
    )
    aggregate_political_bias_label: PoliticalBiasLabel = Field(
        ..., description="Human-readable label for the aggregate bias"
    )
    credibility_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Composite credibility score (0–1) based on source authority, "
            "source diversity, and cross-article factual consensus."
        ),
    )

    # Detailed articles
    articles: list[Article] = Field(
        ...,
        description="Full aggregated articles that belong to this topic",
    )

    # Metadata
    article_count: int = Field(
        ..., ge=0,
        description="Total number of raw source articles ingested into this topic"
    )
    source_count: int = Field(
        ..., ge=0,
        description="Number of distinct news sources contributing to this topic"
    )
    created_at: Optional[str] = Field(None)
    tags: list[str] = Field(default_factory=list)
