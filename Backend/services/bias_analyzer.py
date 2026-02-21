"""
Bias Analyser (stub)

Production implementation would:
  1. Use a fine-tuned classifier (e.g. roberta-base fine-tuned on AllSides/AdFontes data)
     to predict per-article political leaning from text.
  2. Combine text-based prediction with a static source-bias lookup table
     (AllSides Media Bias Ratings, Ad Fontes Media Bias Chart).
  3. Provide segment-level bias by averaging contributing source biases,
     weighted by chunk relevance scores from the embedding stage.

Install (when implementing):
    pip install transformers torch
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Static source-bias lookup (AllSides / Ad Fontes approximations)
# Values are on the scale: -1 (far-left) … 0 (center) … +1 (far-right)
# ---------------------------------------------------------------------------
SOURCE_BIAS_TABLE: dict[str, float] = {
    "Reuters":                   0.02,
    "Associated Press":          0.01,
    "BBC News":                 -0.09,
    "Bloomberg":                 0.18,
    "The Wall Street Journal":   0.22,
    "Financial Times":           0.21,
    "The New York Times":       -0.31,
    "The Guardian":             -0.28,
    "Washington Post":          -0.25,
    "NPR":                      -0.15,
    "TechCrunch":               -0.16,
    "Wired":                    -0.19,
    "CNBC":                      0.05,
    "Fox News":                  0.58,
    "Fox Business":              0.48,
    "Breitbart":                 0.82,
    "The Federalist":            0.65,
    "Mother Jones":             -0.72,
    "HuffPost":                 -0.45,
    "Politico":                 -0.12,
}

DEFAULT_BIAS = 0.0  # Unknown source defaults to neutral


def lookup_source_bias(source_name: str) -> float:
    """Return the known political bias score for a source, or DEFAULT_BIAS if unknown."""
    return SOURCE_BIAS_TABLE.get(source_name, DEFAULT_BIAS)


def aggregate_bias(bias_scores: list[float], weights: list[float] | None = None) -> float:
    """
    Compute a weighted average of political bias scores.

    Args:
        bias_scores: List of per-source bias scores.
        weights: Optional credibility or relevance weights. Defaults to uniform.

    Returns:
        Weighted average bias score in [-1, 1].
    """
    if not bias_scores:
        return DEFAULT_BIAS
    if weights is None:
        weights = [1.0] * len(bias_scores)
    total_weight = sum(weights)
    if total_weight == 0:
        return DEFAULT_BIAS
    return round(sum(b * w for b, w in zip(bias_scores, weights)) / total_weight, 4)


def classify_article_bias_from_text(text: str) -> float:
    """
    STUB: predict political bias from article text using an NLP classifier.

    Production: load a fine-tuned transformer model and run inference.
    Returns a score in [-1, 1].
    """
    # Naive keyword heuristic as placeholder
    left_keywords = ["inequality", "climate justice", "systemic racism", "workers' rights"]
    right_keywords = ["border security", "tax cuts", "free market", "second amendment"]
    text_lower = text.lower()
    left_hits = sum(1 for kw in left_keywords if kw in text_lower)
    right_hits = sum(1 for kw in right_keywords if kw in text_lower)
    net = right_hits - left_hits
    return max(-1.0, min(1.0, net * 0.2))
