"""
scoring/pipeline.py

Orchestrates the full ML → Gemini pipeline and exposes a simple cache so the
FastAPI server can serve results immediately while a background thread runs.

Usage (from main.py):
    from backend.scoring.pipeline import start_background_pipeline, get_cached_stories
"""

import os
import threading
from collections import defaultdict

# ---------------------------------------------------------------------------
# Known-source reputation table (0 = low trust, 1 = high trust)
# ---------------------------------------------------------------------------
SOURCE_REPUTATION: dict[str, float] = {
    "reuters":          0.92,
    "bbc news":         0.88,
    "bbc":              0.88,
    "the guardian":     0.82,
    "guardian":         0.82,
    "financial times":  0.85,
    "ft":               0.85,
    "al jazeera":       0.76,
    "politico":         0.74,
    "the new york times": 0.80,
    "nytimes":          0.80,
    "associated press": 0.90,
    "ap":               0.90,
}

# ---------------------------------------------------------------------------
# Pipeline cache
# ---------------------------------------------------------------------------
_stories_cache: list = []
_status: dict = {"state": "idle", "error": None}
_lock = threading.Lock()


def get_cached_stories() -> list:
    """Return the currently cached StoryWrapper-compatible dicts (may be empty while running)."""
    with _lock:
        return list(_stories_cache)


def get_pipeline_status() -> dict:
    with _lock:
        return dict(_status)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def run_pipeline(articles_dir: str) -> list:
    """
    Full scoring pipeline for a directory of .txt articles.

    Steps:
      1. Load articles from articles_dir
      2. Sentiment scoring (objectivity / subjectivity per article)
      3. Agreement scoring (entailment / contradiction / missing context)
      4. Credibility scoring (composite per article)
      5. Gemini aggregation → StoryWrapper dict
      6. Persist to stories.json

    Returns a list containing the single StoryWrapper dict produced for the
    article set.  Raises on unrecoverable errors.
    """
    # --- local imports to avoid eager model loading at startup ---
    from .sentiment_scoring import score_article
    from .agreement_scoring import load_articles, compute_agreement
    from .credibility_scoring import compute_article_credibility
    from .gemini_article_aggregator import (
        load_api_key,
        load_articles as gemini_load_articles,
        build_prompt,
        call_gemini,
        gemini_to_storywrapper,
        save_story_to_json,
    )

    # 1. Load raw articles
    articles = load_articles(articles_dir)
    if not articles:
        raise FileNotFoundError(f"No .txt files found in {articles_dir!r}")

    # Attach known reputation scores (fall back to 0.5)
    for art in articles:
        src_key = art.get("source", "").lower()
        art["reputation"] = SOURCE_REPUTATION.get(src_key, 0.5)

    # 2. Sentiment scoring
    for art in articles:
        obj, subj = score_article(art["text"])
        art["objectivity"] = obj
        art["subjectivity"] = subj

    # 3. Agreement scoring
    agreement_scores, contradiction_reports, missing_context = compute_agreement(articles)

    # 4. Credibility scoring
    contradictions_per_article = defaultdict(list)
    for report in contradiction_reports:
        contradictions_per_article[report["wrong_article"]].append(report)

    credibility_scores: dict[str, float] = {}
    for art in articles:
        credibility_scores[art["id"]] = compute_article_credibility(
            art,
            agreement_scores,
            contradictions_per_article,
            missing_context,
        )

    # Build provider_trust_map from article source metadata
    provider_trust_map: dict[str, float] = {
        art["source"]: credibility_scores[art["id"]]
        for art in articles
        if art.get("source") and art["source"] != "unknown"
    }

    # 5. Gemini aggregation
    api_key = load_api_key()
    gemini_articles = gemini_load_articles(articles_dir)
    prompt = build_prompt(gemini_articles)
    gemini_result = call_gemini(api_key, prompt)

    story_dict = gemini_to_storywrapper(
        gemini_result,
        credibility_scores=credibility_scores,
        provider_trust_map=provider_trust_map,
    )

    # 6. Persist
    save_story_to_json(story_dict)

    return [story_dict]


# ---------------------------------------------------------------------------
# Background thread management
# ---------------------------------------------------------------------------

def _pipeline_worker(articles_dir: str) -> None:
    global _stories_cache, _status
    try:
        with _lock:
            _status = {"state": "running", "error": None}
        print(f"[pipeline] Starting pipeline for {articles_dir!r} …")
        results = run_pipeline(articles_dir)
        with _lock:
            _stories_cache = results
            _status = {"state": "done", "error": None}
        print(f"[pipeline] Done — {len(results)} story/stories cached.")
    except Exception as exc:
        with _lock:
            _status = {"state": "error", "error": str(exc)}
        print(f"[pipeline] ERROR: {exc}")


def start_background_pipeline(articles_dir: str | None = None) -> None:
    """
    Spawn a daemon thread that runs the full pipeline.
    Results are stored in the module-level cache and retrievable via
    get_cached_stories().

    articles_dir defaults to backend/scoring/test if not provided.
    """
    if articles_dir is None:
        articles_dir = os.path.join(os.path.dirname(__file__), "test")

    thread = threading.Thread(
        target=_pipeline_worker,
        args=(articles_dir,),
        daemon=True,
        name="scoring-pipeline",
    )
    thread.start()


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    articles_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "test")
    print(f"[pipeline] Running standalone for: {articles_dir}")
    try:
        results = run_pipeline(articles_dir)
        print(f"[pipeline] Complete — {len(results)} story/stories produced.")
    except Exception as exc:
        print(f"[pipeline] Failed: {exc}")
        sys.exit(1)
