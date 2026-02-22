# credibility_scoring.py

import os
from collections import defaultdict

# Support both standalone execution and package import
try:
    from .sentiment_scoring import score_article
    from .agreement_scoring import load_articles, compute_agreement
except ImportError:
    from sentiment_scoring import score_article       # type: ignore
    from agreement_scoring import load_articles, compute_agreement  # type: ignore

DEFAULT_ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "test")

# Weights for credibility
WEIGHT_REPUTATION = 0.4
WEIGHT_OBJECTIVITY = 0.3
WEIGHT_AGREEMENT = 0.3

def compute_article_credibility(article, agreement_score, contradictions, missing_context):
    """
    Computes a final credibility score per article.
    Penalizes for contradictions and missing context.
    """
    rep = article.get("reputation", 0.5)
    obj = article.get("objectivity", 0.5)
    agree = agreement_score.get(article["id"], 0)

    # Basic weighted score
    credibility = (WEIGHT_REPUTATION * rep +
                   WEIGHT_OBJECTIVITY * obj +
                   WEIGHT_AGREEMENT * agree)

    # Penalize for contradictions or missing context
    if article["id"] in contradictions:
        credibility -= 0.2  # higher penalty for contradictions
    if article["id"] in missing_context and len(missing_context[article["id"]]) > 0:
        credibility -= 0.1  # smaller penalty for missing context

    return round(max(credibility, 0), 3)  # ensure not negative

def main():
    import sys
    articles_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ARTICLES_DIR
    # Step 1: Load articles
    articles = load_articles(articles_dir)

    # Step 2: Score objectivity/subjectivity
    for article in articles:
        obj, subj = score_article(article["text"])
        article["objectivity"] = obj
        article["subjectivity"] = subj

    # Step 3: Compute agreement, contradictions, missing context
    agreement_score, contradiction_reports, missing_context = compute_agreement(articles)

    # Step 4: Map contradictions per article
    contradictions_per_article = defaultdict(list)
    for report in contradiction_reports:
        contradictions_per_article[report["wrong_article"]].append(report)

    # Step 5: Compute credibility per article
    credibility_scores = {}
    for article in articles:
        credibility_scores[article["id"]] = compute_article_credibility(
            article,
            agreement_score,
            contradictions_per_article,
            missing_context
        )

    # ==============================
    # OUTPUT (can be saved per article for website)
    # ==============================
    for article in articles:
        aid = article["id"]
        print(f"\n=== {aid} ===")
        print(f"Credibility Score: {credibility_scores[aid]}")
        print(f"Objectivity: {round(article['objectivity'],3)} | Subjectivity: {round(article['subjectivity'],3)}")
        print(f"Missing Context: {len(missing_context.get(aid, []))} claims")
        print(f"Contradictions: {len(contradictions_per_article.get(aid, []))}")
        # Show some example claims
        for c in missing_context.get(aid, [])[:3]:
            print("-", c)
        for c in contradictions_per_article.get(aid, [])[:3]:
            print("Wrong claim:", c["wrong_claim"])
            print("Contradicted by:", c["correct_article"])

if __name__ == "__main__":
    main()