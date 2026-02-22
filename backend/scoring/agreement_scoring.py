"""
agreement_scoring.py

Cross-article claim agreement / contradiction pipeline.

Uses:
  • sentence-transformers/all-MiniLM-L6-v2  — claim embedding & similarity
  • facebook/bart-large-mnli                 — NLI (entailment / contradiction)
  • GroNLP/mdebertav3-subjectivity-english   — (shared via sentiment_scoring)

Public API:
    load_articles(articles_dir: str) -> list[dict]
        Load .txt files from a directory, return list of article dicts with
        id, text, objectivity, subjectivity (scored via sentiment_scoring).

    compute_agreement(articles: list[dict])
        -> tuple[agreement_scores, contradiction_reports, missing_context]

        agreement_scores   : dict[article_id -> float]  (clipped to 0–1)
        contradiction_reports : list[dict]
        missing_context    : dict[article_id -> list[str]]

All heavy models are loaded lazily on first call.
"""

from __future__ import annotations

import itertools
import re
from collections import defaultdict

import nltk
import numpy as np

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# Shared subjectivity scorer from sentiment_scoring
try:
    from .sentiment_scoring import score_sentence, score_article as _score_article
except ImportError:
    from sentiment_scoring import score_sentence, score_article as _score_article

# ── Config ────────────────────────────────────────────────────────────────────

SIMILARITY_THRESHOLD = 0.75
CLAIM_OBJECTIVITY_THRESHOLD = 0.6
MISSING_CONTEXT_SIM_THRESHOLD = 0.8
DEFAULT_REPUTATION = 0.5

# ── Lazy model loader ─────────────────────────────────────────────────────────

_models: dict = {}


def _get_models() -> dict:
    if not _models:
        import torch
        from sentence_transformers import SentenceTransformer
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        print("[agreement_scoring] Loading embedding model…", flush=True)
        _models["embedder"] = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        print("[agreement_scoring] Loading NLI model…", flush=True)
        nli_name = "facebook/bart-large-mnli"
        _models["nli_tokenizer"] = AutoTokenizer.from_pretrained(nli_name)
        _models["nli_model"] = AutoModelForSequenceClassification.from_pretrained(
            nli_name
        )
        _models["device"] = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        _models["nli_model"].to(_models["device"])
        print("[agreement_scoring] Models ready.", flush=True)
    return _models


# ── Helpers ───────────────────────────────────────────────────────────────────


def extract_claims(article: dict) -> list[dict]:
    """Extract high-objectivity factual claims from an article."""
    sentences = nltk.sent_tokenize(article["text"])
    claims = []
    for s in sentences:
        obj, _ = score_sentence(s)
        if (
            obj >= CLAIM_OBJECTIVITY_THRESHOLD
            and len(s.split()) > 6
            and not s.strip().endswith("?")
        ):
            claims.append({"text": s.strip(), "objectivity": obj})
    return claims


def _classify_nli(claim1: str, claim2: str) -> str:
    import torch

    m = _get_models()
    inputs = m["nli_tokenizer"](
        claim1, claim2, return_tensors="pt", truncation=True
    ).to(m["device"])
    outputs = m["nli_model"](**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    labels = ["contradiction", "neutral", "entailment"]
    return labels[torch.argmax(probs)]


def _has_different_numbers(claim1: str, claim2: str) -> bool:
    nums1 = re.findall(r"\d+", claim1)
    nums2 = re.findall(r"\d+", claim2)
    if not nums1 or not nums2:
        return False
    return not any(n in nums2 for n in nums1)


# ── Public API ────────────────────────────────────────────────────────────────


def load_articles(articles_dir: str) -> list[dict]:
    """
    Load all .txt files from *articles_dir*.
    Each article is scored for objectivity/subjectivity.
    """
    import os

    articles = []
    for filename in sorted(os.listdir(articles_dir)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(articles_dir, filename)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        obj, subj = _score_article(text)
        articles.append(
            {
                "id": filename,
                "text": text,
                "source": "unknown",
                "reputation": DEFAULT_REPUTATION,
                "objectivity": obj,
                "subjectivity": subj,
            }
        )
    return articles


def compute_agreement(
    articles: list[dict],
) -> tuple[dict, list, dict]:
    """
    Run the full agreement pipeline.

    Args:
        articles: list of dicts with keys:
            id          – unique article identifier (filename)
            text        – article body text
            objectivity – pre-computed objectivity score (0–1)
            subjectivity – pre-computed subjectivity score (0–1)

    Returns:
        (agreement_scores, contradiction_reports, missing_context)

        agreement_scores:  dict[id -> float in 0–1]
        contradiction_reports: list[dict] with wrong/correct article + claim
        missing_context:   dict[id -> list[str]] (missing core claims)
    """
    from sentence_transformers import util

    models = _get_models()
    embedder = models["embedder"]

    # ── Extract claims ────────────────────────────────────────────────────────
    for article in articles:
        if "claims" not in article:
            article["claims"] = extract_claims(article)

    all_claims: list[str] = []
    claim_meta: list[dict] = []
    for article in articles:
        for claim in article["claims"]:
            all_claims.append(claim["text"])
            claim_meta.append(
                {
                    "article_id": article["id"],
                    "article_obj": article["objectivity"],
                    "claim_obj": claim["objectivity"],
                }
            )

    if not all_claims:
        empty: dict = {a["id"]: 0.5 for a in articles}
        return empty, [], {a["id"]: [] for a in articles}

    # ── Embed claims ──────────────────────────────────────────────────────────
    claim_embeddings = embedder.encode(all_claims, convert_to_tensor=True)

    # ── Compare claim pairs ───────────────────────────────────────────────────
    truth_votes: dict = defaultdict(float)
    article_support: dict = defaultdict(float)
    article_contradiction: dict = defaultdict(float)
    contradictions_list: list = []

    for i, j in itertools.combinations(range(len(all_claims)), 2):
        sim = util.cos_sim(claim_embeddings[i], claim_embeddings[j]).item()
        if sim <= SIMILARITY_THRESHOLD:
            continue
        if _has_different_numbers(all_claims[i], all_claims[j]):
            continue

        result = _classify_nli(all_claims[i], all_claims[j])
        if result not in ("entailment", "contradiction"):
            continue

        wi = claim_meta[i]["article_obj"] * claim_meta[i]["claim_obj"]
        wj = claim_meta[j]["article_obj"] * claim_meta[j]["claim_obj"]

        if result == "entailment":
            truth_votes[i] += wj
            truth_votes[j] += wi
            article_support[claim_meta[i]["article_id"]] += wj
            article_support[claim_meta[j]["article_id"]] += wi
        else:  # contradiction
            truth_votes[i] -= wj
            truth_votes[j] -= wi
            article_contradiction[claim_meta[i]["article_id"]] += wj
            article_contradiction[claim_meta[j]["article_id"]] += wi
            contradictions_list.append((i, j))

    # ── Per-article scores ────────────────────────────────────────────────────
    raw_scores: dict = {}
    for article in articles:
        aid = article["id"]
        total_weight = sum(c["objectivity"] for c in article["claims"]) or 1.0
        supported = article_support.get(aid, 0.0)
        contradicted = article_contradiction.get(aid, 0.0)
        consistency = (
            (supported - contradicted) / total_weight
            + 0.5 * article["objectivity"]
        )
        raw_scores[aid] = consistency

    # Normalise to 0–1
    agreement_scores = {
        aid: float(np.clip(score, 0.0, 1.0))
        for aid, score in raw_scores.items()
    }

    # ── Missing context detection ─────────────────────────────────────────────
    threshold = (
        float(np.percentile(list(truth_votes.values()), 75))
        if truth_votes
        else 0.0
    )
    core_claims_idx = [idx for idx, v in truth_votes.items() if v > threshold]

    missing_context: dict = defaultdict(list)
    for idx in core_claims_idx:
        claim_embed = claim_embeddings[idx]
        for article in articles:
            found = False
            for sent in nltk.sent_tokenize(article["text"]):
                sent_embed = embedder.encode(sent, convert_to_tensor=True)
                if (
                    util.cos_sim(claim_embed, sent_embed).item()
                    > MISSING_CONTEXT_SIM_THRESHOLD
                ):
                    found = True
                    break
            if not found:
                missing_context[article["id"]].append(all_claims[idx])

    # ── Contradiction reports ─────────────────────────────────────────────────
    contradiction_reports: list = []
    for i, j in contradictions_list:
        wi = claim_meta[i]["article_obj"] * claim_meta[i]["claim_obj"]
        wj = claim_meta[j]["article_obj"] * claim_meta[j]["claim_obj"]
        if wi <= wj:
            wrong, correct = i, j
        else:
            wrong, correct = j, i
        contradiction_reports.append(
            {
                "wrong_article": claim_meta[wrong]["article_id"],
                "wrong_claim": all_claims[wrong],
                "correct_article": claim_meta[correct]["article_id"],
                "correct_claim": all_claims[correct],
            }
        )

    return agreement_scores, contradiction_reports, dict(missing_context)


# ── Standalone entry point ────────────────────────────────────────────────────


def main() -> None:
    import os

    articles_dir = os.path.join(os.path.dirname(__file__), "test")
    articles = load_articles(articles_dir)
    agreement_scores, contradiction_reports, missing_context = compute_agreement(
        articles
    )

    print("\n==== Agreement Scores ====")
    for aid, score in agreement_scores.items():
        print(f"  {aid}: {score:.3f}")

    print("\n==== Missing Context ====")
    for aid, claims in missing_context.items():
        print(f"  {aid}: {len(claims)} missing core claims")

    print("\n==== Contradictions ====")
    for r in contradiction_reports:
        print(f"  WRONG: {r['wrong_article']}  |  {r['wrong_claim'][:80]}")


if __name__ == "__main__":
    main()
