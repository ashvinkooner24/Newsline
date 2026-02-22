"""
sentiment_scoring.py

Scores article text for subjectivity / objectivity using
GroNLP/mdebertav3-subjectivity-english.

Public API (importable from pipeline):
    score_article(text: str) -> tuple[float, float]
        Returns (objectivity, subjectivity) in 0–1 range.
    score_sentence(sentence: str) -> tuple[float, float]
        Returns (objectivity, subjectivity) for one sentence.

Models are loaded lazily on first call so importing this module does NOT
trigger any network/disk activity at server startup.
"""

from __future__ import annotations

import nltk

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# ── Lazy model loader ─────────────────────────────────────────────────────────

_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline as hf_pipeline

        print("[sentiment_scoring] Loading subjectivity model…", flush=True)
        _classifier = hf_pipeline(
            "text-classification",
            model="GroNLP/mdebertav3-subjectivity-english",
            top_k=None,
        )
        print("[sentiment_scoring] Model ready.", flush=True)
    return _classifier


# ── Public API ────────────────────────────────────────────────────────────────


def score_sentence(sentence: str) -> tuple[float, float]:
    """Returns (objectivity, subjectivity) for a single sentence (0–1 each)."""
    clf = _get_classifier()
    result = clf(sentence)[0]
    subj = next(
        (float(item["score"]) for item in result if item["label"] == "LABEL_1"),
        0.5,
    )
    return 1.0 - subj, subj


def score_article(text: str) -> tuple[float, float]:
    """
    Returns (objectivity, subjectivity) for a full article.
    Scores are weighted by sentence word-count so longer sentences
    have proportionally more influence.
    """
    from nltk.tokenize import sent_tokenize

    sentences = sent_tokenize(text)
    if not sentences:
        return 0.5, 0.5

    weighted_obj = 0.0
    total_words = 0
    for s in sentences:
        obj, _ = score_sentence(s)
        w = len(s.split())
        weighted_obj += obj * w
        total_words += w

    objectivity = weighted_obj / total_words if total_words > 0 else 0.5
    return objectivity, 1.0 - objectivity


# ── Standalone entry point ────────────────────────────────────────────────────


def main() -> None:
    import os

    test_dir = os.path.join(os.path.dirname(__file__), "test")
    for filename in sorted(os.listdir(test_dir)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(test_dir, filename)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        obj, subj = score_article(text)
        print(f"{filename}: objectivity={obj:.2%}  subjectivity={subj:.2%}")


if __name__ == "__main__":
    main()
