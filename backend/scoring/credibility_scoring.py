"""
credibility_scoring.py

Computes a composite credibility score for each article:
    credibility = 0.4 × reputation + 0.3 × objectivity + 0.3 × agreement
    − 0.2 (if article has contradictions)
    − 0.1 (if article has missing context)

Score is clipped to [0, 1].

Public API:
    compute_article_credibility(article, agreement_scores,
                                contradiction_reports, missing_context)
        -> float (0–1)

    run_credibility_scoring(articles, agreement_scores,
                            contradiction_reports, missing_context)
        -> dict[article_id -> float]
"""

from __future__ import annotations

from collections import defaultdict

# ── Weights ───────────────────────────────────────────────────────────────────

WEIGHT_REPUTATION = 0.4
WEIGHT_OBJECTIVITY = 0.3
WEIGHT_AGREEMENT = 0.3

# ── Public API ────────────────────────────────────────────────────────────────


def compute_article_credibility(
    article: dict,
    agreement_scores: dict,
    contradiction_reports: list,
    missing_context: dict,
) -> float:
    """
    Returns a credibility score in [0, 1] for *article*.

    Args:
        article:             dict with keys id, objectivity, reputation
        agreement_scores:    dict[article_id -> float (0–1)]
        contradiction_reports: list of contradiction report dicts
        missing_context:     dict[article_id -> list[str]]
    """
    rep = float(article.get("reputation", 0.5))
    obj = float(article.get("objectivity", 0.5))
    agree = float(agreement_scores.get(article["id"], 0.5))

    credibility = (
        WEIGHT_REPUTATION * rep
        + WEIGHT_OBJECTIVITY * obj
        + WEIGHT_AGREEMENT * agree
    )

    # Penalties
    contradicted_ids = {r["wrong_article"] for r in contradiction_reports}
    if article["id"] in contradicted_ids:
        credibility -= 0.2

    if missing_context.get(article["id"]):
        credibility -= 0.1

    return round(max(0.0, min(1.0, credibility)), 3)


def run_credibility_scoring(
    articles: list[dict],
    agreement_scores: dict,
    contradiction_reports: list,
    missing_context: dict,
) -> dict:
    """
    Compute credibility score for every article in the list.
    Returns dict[article_id -> float (0–1)].
    """
    return {
        a["id"]: compute_article_credibility(
            a, agreement_scores, contradiction_reports, missing_context
        )
        for a in articles
    }


# ── Standalone entry point ────────────────────────────────────────────────────


def main() -> None:
    import os

    # When run as a script, load scoring modules via sys.path
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from agreement_scoring import compute_agreement, load_articles
    from sentiment_scoring import score_article

    articles_dir = os.path.join(os.path.dirname(__file__), "test")
    articles = load_articles(articles_dir)

    # Re-score objectivity (load_articles already does this, but
    # kept explicit for clarity)
    for article in articles:
        article["objectivity"], article["subjectivity"] = score_article(
            article["text"]
        )

    agreement_scores, contradiction_reports, missing_context = compute_agreement(
        articles
    )
    credibility_scores = run_credibility_scoring(
        articles, agreement_scores, contradiction_reports, missing_context
    )

    for article in articles:
        aid = article["id"]
        print(f"\n=== {aid} ===")
        print(f"  Credibility : {credibility_scores[aid]:.3f}")
        print(
            f"  Objectivity : {article['objectivity']:.3f} | "
            f"Subjectivity: {article['subjectivity']:.3f}"
        )
        print(f"  Agreement   : {agreement_scores.get(aid, 0):.3f}")
        print(f"  Missing ctx : {len(missing_context.get(aid, []))}")


if __name__ == "__main__":
    main()
