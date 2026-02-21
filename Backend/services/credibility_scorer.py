"""
Credibility Scorer (stub)

Production implementation would combine three signals:

  1. SOURCE AUTHORITY  — static credibility ratings from NewsGuard, MBFC (Media
     Bias/Fact Check), or a custom human-labelled dataset (pre-seeded from the
     SOURCE_CREDIBILITY_TABLE below).

  2. SOURCE DIVERSITY  — entropy of the source distribution for a topic.
     Topics backed by 10 outlets with varied ownership score higher than those
     backed by 2 outlets from the same parent company.

  3. CROSS-ARTICLE CONSENSUS — semantic similarity between claims made in
     different articles. High variance across sources reduces confidence.
     In production, this leverages stored chunk embeddings to compute
     pairwise agreement scores at the claim level.

Final score: credibility = 0.5 * authority + 0.25 * diversity + 0.25 * consensus
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# Static source authority lookup (NewsGuard / MBFC approximations to 0–1)
# ---------------------------------------------------------------------------
SOURCE_CREDIBILITY_TABLE: dict[str, float] = {
    "Reuters":                   0.92,
    "Associated Press":          0.93,
    "BBC News":                  0.90,
    "Bloomberg":                 0.91,
    "The Wall Street Journal":   0.88,
    "Financial Times":           0.88,
    "The New York Times":        0.85,
    "The Guardian":              0.86,
    "Washington Post":           0.85,
    "NPR":                       0.87,
    "TechCrunch":                0.82,
    "Wired":                     0.83,
    "CNBC":                      0.84,
    "Fox News":                  0.72,
    "Fox Business":              0.77,
    "Breitbart":                 0.38,
    "The Federalist":            0.48,
    "Mother Jones":              0.65,
    "HuffPost":                  0.70,
    "Politico":                  0.83,
}

DEFAULT_CREDIBILITY = 0.60


def source_authority_score(source_names: list[str]) -> float:
    """Mean authority score across a set of sources."""
    if not source_names:
        return DEFAULT_CREDIBILITY
    scores = [SOURCE_CREDIBILITY_TABLE.get(n, DEFAULT_CREDIBILITY) for n in source_names]
    return round(sum(scores) / len(scores), 4)


def source_diversity_score(source_names: list[str]) -> float:
    """
    Normalised Shannon entropy of source distribution.
    Returns 0.0 for a single source and 1.0 for perfectly uniform distribution.
    """
    if not source_names:
        return 0.0
    from collections import Counter

    counts = Counter(source_names)
    total = len(source_names)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return round(entropy / max_entropy, 4) if max_entropy > 0 else 1.0


def cross_article_consensus_score(claim_embeddings: list[list[float]]) -> float:
    """
    STUB: estimate factual consensus across articles using embedding similarity.

    Production: compute pairwise cosine similarities between claim chunk embeddings
    and return mean similarity as a proxy for cross-source agreement.
    """
    if len(claim_embeddings) < 2:
        return 1.0  # No divergence possible with one source
    # Placeholder — real implementation uses stored vectors
    return 0.80


def composite_credibility_score(
    source_names: list[str],
    claim_embeddings: list[list[float]] | None = None,
) -> float:
    """
    Compute the composite credibility score for a topic or article.

    Formula: 0.50 * authority + 0.25 * diversity + 0.25 * consensus
    """
    authority = source_authority_score(source_names)
    diversity = source_diversity_score(source_names)
    consensus = cross_article_consensus_score(claim_embeddings or [])
    score = 0.50 * authority + 0.25 * diversity + 0.25 * consensus
    return round(min(1.0, max(0.0, score)), 4)
