"""
pipeline.py

Full scoring + aggregation pipeline for The Newsline.

Flow
----
1.  Load raw article .txt files from ARTICLES_DIR
2.  Score each article with sentiment_scoring  (objectivity / subjectivity)
3.  Run cross-article agreement_scoring        (consistency, contradictions,
                                                missing context)
4.  Compute per-article credibility_scoring    (composite 0–1 score)
5.  Call gemini_article_aggregator             (consolidated story + citations)
6.  Assemble a TopicSummary Pydantic object for the API

The pipeline runs in a background thread at server startup.
Results are cached in module-level `_topics`.  The API returns cached data
immediately; a fallback is used while the pipeline is still running.

Public API
----------
start_background_pipeline() – spawn the background thread (call once)
get_topics()               – return cached list[TopicSummary] (may be [])
pipeline_status()          – dict with running / done / error flags
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from statistics import mean
from typing import Optional

# Project root is 3 levels up from this file (backend/scoring/pipeline.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLES_DIR = os.path.join(SCRIPT_DIR, "test")

# ── Source metadata ───────────────────────────────────────────────────────────
# bias_score: -1 (far-left) … +1 (far-right)
# reputation:  0 (low) … 1 (high)

SOURCE_METADATA: dict[str, dict] = {
    "The Guardian": {
        "id": "guardian",
        "url": "https://theguardian.com",
        "bias_lean": "center-left",
        "bias_score": -0.25,
        "reputation": 0.82,
        "country": "UK",
    },
    "Reuters": {
        "id": "reuters",
        "url": "https://reuters.com",
        "bias_lean": "center",
        "bias_score": 0.0,
        "reputation": 0.92,
        "country": "UK",
    },
    "BBC News": {
        "id": "bbc",
        "url": "https://bbc.co.uk",
        "bias_lean": "center",
        "bias_score": 0.0,
        "reputation": 0.88,
        "country": "UK",
    },
    "Financial Times": {
        "id": "ft",
        "url": "https://ft.com",
        "bias_lean": "center-right",
        "bias_score": 0.20,
        "reputation": 0.87,
        "country": "UK",
    },
    "Al Jazeera": {
        "id": "aljazeera",
        "url": "https://aljazeera.com",
        "bias_lean": "center-left",
        "bias_score": -0.20,
        "reputation": 0.75,
        "country": "Qatar",
    },
    "Politico": {
        "id": "politico",
        "url": "https://politico.eu",
        "bias_lean": "center-left",
        "bias_score": -0.15,
        "reputation": 0.80,
        "country": "US",
    },
}

# ── Cache ─────────────────────────────────────────────────────────────────────

_topics: list = []          # list[TopicSummary]
_status: dict = {"running": False, "done": False, "error": None}
_lock = threading.Lock()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _bias_float_to_lean(score: float) -> str:
    if score < -0.6:
        return "far-left"
    if score < -0.3:
        return "left"
    if score < -0.1:
        return "center-left"
    if score <= 0.1:
        return "center"
    if score <= 0.3:
        return "center-right"
    if score <= 0.6:
        return "right"
    return "far-right"


def _slugify(text: str) -> str:
    import re

    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _default_meta(source_name: str) -> dict:
    return {
        "id": _slugify(source_name),
        "url": "#",
        "bias_lean": "center",
        "bias_score": 0.0,
        "reputation": 0.5,
        "country": "Unknown",
    }


# ── Pipeline steps ────────────────────────────────────────────────────────────


def _load_raw_articles(articles_dir: str) -> list[dict]:
    """Load article texts and attach source metadata."""
    from .gemini_article_aggregator import SOURCE_BY_FILENAME

    articles = []
    for filename in sorted(os.listdir(articles_dir)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(articles_dir, filename)
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read().strip()
        source_name = SOURCE_BY_FILENAME.get(filename, f"Unknown ({filename})")
        meta = SOURCE_METADATA.get(source_name, _default_meta(source_name))
        articles.append(
            {
                "article_id": filename,
                "id": filename,           # alias for agreement_scoring compat
                "source": source_name,
                "content": content,
                "text": content,          # alias for agreement_scoring compat
                "reputation": meta["reputation"],
                "bias_score": meta["bias_score"],
            }
        )
    return articles


def _run_sentiment(articles: list[dict]) -> None:
    """Score each article in-place: adds objectivity + subjectivity keys."""
    from .sentiment_scoring import score_article

    print(f"[pipeline] Scoring sentiment for {len(articles)} articles…", flush=True)
    for art in articles:
        obj, subj = score_article(art["content"])
        art["objectivity"] = obj
        art["subjectivity"] = subj
        print(f"  {art['article_id']}: obj={obj:.2%} subj={subj:.2%}", flush=True)


def _run_agreement(articles: list[dict]) -> tuple[dict, list, dict]:
    from .agreement_scoring import compute_agreement

    print("[pipeline] Running agreement scoring…", flush=True)
    agreement_scores, contradiction_reports, missing_context = compute_agreement(
        articles
    )
    print(
        f"  agreement done — {len(contradiction_reports)} contradictions found",
        flush=True,
    )
    return agreement_scores, contradiction_reports, missing_context


def _run_credibility(
    articles: list[dict],
    agreement_scores: dict,
    contradiction_reports: list,
    missing_context: dict,
) -> dict:
    from .credibility_scoring import run_credibility_scoring

    print("[pipeline] Computing credibility scores…", flush=True)
    scores = run_credibility_scoring(
        articles, agreement_scores, contradiction_reports, missing_context
    )
    for aid, s in scores.items():
        print(f"  {aid}: credibility={s:.3f}", flush=True)
    return scores


def _run_gemini(articles: list[dict]) -> dict:
    from .gemini_article_aggregator import (
        build_prompt,
        call_gemini,
        load_api_key,
    )

    print("[pipeline] Calling Gemini aggregator…", flush=True)
    api_key = load_api_key()
    gemini_articles = [
        {"article_id": a["article_id"], "source": a["source"], "content": a["content"]}
        for a in articles
    ]
    prompt = build_prompt(gemini_articles)
    result = call_gemini(api_key, prompt)
    print(f"  Gemini done — title: {result.get('title', '?')[:60]}", flush=True)
    return result


# ── TopicSummary builder ──────────────────────────────────────────────────────


def _build_topic_summary(
    gemini_result: dict,
    articles: list[dict],
    credibility_scores: dict,
    agreement_scores: dict,
    missing_context: dict,
    contradiction_reports: list,
):
    """Assemble a TopicSummary Pydantic model from all pipeline outputs."""
    from ..models import (
        Article,
        BiasAnalysis,
        Citation,
        CredibilityAssessment,
        FactCheck,
        NewsSource,
        SectionStats,
        SummarySection,
        ToneScore,
        TopicSummary,
    )

    article_by_id = {a["article_id"]: a for a in articles}
    contradicted_ids = {r["wrong_article"] for r in contradiction_reports}
    now_str = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── Build Article objects ─────────────────────────────────────────────────
    frontend_articles: list[Article] = []
    seen: set = set()
    for entry in gemini_result.get("source_index", []):
        aid = entry["article_id"]
        if aid in seen:
            continue
        seen.add(aid)
        raw = article_by_id.get(aid)
        if not raw:
            continue

        meta = SOURCE_METADATA.get(raw["source"], _default_meta(raw["source"]))
        cred_0_1 = credibility_scores.get(aid, meta["reputation"])
        subjectivity = raw.get("subjectivity", 0.5)
        objectivity = raw.get("objectivity", 0.5)

        # Verdict
        if aid in contradicted_ids:
            verdict = "misleading"
        elif subjectivity > 0.6:
            verdict = "mixed"
        elif missing_context.get(aid):
            verdict = "mostly-true"
        else:
            verdict = "verified"

        # Tone label
        if subjectivity > 0.6:
            tone = "emotional"
        elif objectivity > 0.65:
            tone = "analytical"
        else:
            tone = "balanced"

        excerpt = raw["content"][:300].rsplit(" ", 1)[0] + "…"

        frontend_articles.append(
            Article(
                id=aid,
                title=f"{raw['source']}: {gemini_result['title']}",
                url=meta["url"],
                source=NewsSource(
                    id=meta["id"],
                    name=raw["source"],
                    url=meta["url"],
                    credibility_score=round(cred_0_1 * 100, 1),
                    bias_lean=meta["bias_lean"],
                    country=meta["country"],
                ),
                published_at=today_str,
                excerpt=excerpt,
                tone=tone,
                tone_score=ToneScore(
                    emotional=round(subjectivity * 100),
                    logical=round(objectivity * 100),
                ),
                fact_check=FactCheck(
                    verdict=verdict,
                    details=(
                        f"Objectivity: {objectivity:.0%}. "
                        f"Agreement consistency: {agreement_scores.get(aid, 0.5):.2f}."
                    ),
                    missing_context=missing_context.get(aid, [])[:3],
                ),
            )
        )

    # ── Build SummarySections ─────────────────────────────────────────────────
    sections: list[SummarySection] = []
    for sec in gemini_result.get("body_sections", []):
        cited_ids = list(
            dict.fromkeys(c["article_id"] for c in sec.get("citations", []))
        )

        cited_creds = [credibility_scores.get(i, 0.5) for i in cited_ids]
        cited_agrees = [
            float(max(0.0, min(1.0, agreement_scores.get(i, 0.5))))
            for i in cited_ids
        ]
        cited_biases = [
            SOURCE_METADATA.get(
                article_by_id.get(i, {}).get("source", ""), _default_meta("")
            )["bias_score"]
            for i in cited_ids
        ]

        avg_cred = mean(cited_creds) if cited_creds else 0.5
        avg_agree = mean(cited_agrees) if cited_agrees else 0.5
        avg_bias = mean(cited_biases) if cited_biases else 0.0

        sections.append(
            SummarySection(
                heading=sec["heading"],
                content=sec["content"],
                citations=[
                    Citation(
                        article_id=c["article_id"],
                        text=c["quote"],
                        bias_level=c.get("bias_level", "neutral"),
                    )
                    for c in sec.get("citations", [])
                ],
                stats=SectionStats(
                    bias_lean=_bias_float_to_lean(avg_bias),
                    lean_score=round(avg_bias * 100, 1),
                    credibility_score=round(avg_cred * 100, 1),
                    source_count=len(cited_ids),
                    agreement=round(avg_agree * 100, 1),
                ),
            )
        )

    # ── BiasAnalysis ──────────────────────────────────────────────────────────
    all_bias = [
        SOURCE_METADATA.get(a["source"], _default_meta(a["source"]))["bias_score"]
        for a in articles
    ]
    avg_bias_overall = mean(all_bias) if all_bias else 0.0
    bias_analysis = BiasAnalysis(
        overall_lean=_bias_float_to_lean(avg_bias_overall),
        lean_score=round(avg_bias_overall * 100, 1),
        left_source_count=sum(1 for b in all_bias if b < -0.1),
        center_source_count=sum(1 for b in all_bias if -0.1 <= b <= 0.1),
        right_source_count=sum(1 for b in all_bias if b > 0.1),
    )

    # ── CredibilityAssessment ─────────────────────────────────────────────────
    all_creds = [credibility_scores.get(a["article_id"], 0.5) for a in articles]
    all_agrees = [
        float(max(0.0, min(1.0, agreement_scores.get(a["article_id"], 0.5))))
        for a in articles
    ]
    avg_rep = mean(
        SOURCE_METADATA.get(a["source"], _default_meta(a["source"]))["reputation"]
        for a in articles
    )
    avg_cred_overall = mean(all_creds) if all_creds else 0.5
    avg_agree_overall = mean(all_agrees) if all_agrees else 0.5
    cred_score = round(avg_cred_overall * 100, 1)
    cred_label = (
        "High" if cred_score >= 80
        else "Medium" if cred_score >= 60
        else "Low" if cred_score >= 40
        else "Uncertain"
    )
    credibility_assessment = CredibilityAssessment(
        score=cred_score,
        article_count=len(frontend_articles),
        avg_source_credibility=round(avg_rep * 100, 1),
        source_agreement=round(avg_agree_overall * 100, 1),
        label=cred_label,
    )

    # ── Slug / ID ─────────────────────────────────────────────────────────────
    title = gemini_result["title"]
    slug = _slugify(title)
    topic_id = slug[:60]

    return TopicSummary(
        id=topic_id,
        topic=title,
        slug=slug,
        headline=title,
        summary=gemini_result["standfirst"],
        sections=sections,
        articles=frontend_articles,
        bias_analysis=bias_analysis,
        credibility=credibility_assessment,
        updated_at=now_str,
        category="Politics",
        country="UK",
        subtopic="Legislation",
        is_featured=True,
        comments=[],
        community_notes=[],
    )


def _build_topic_summary_without_gemini(
    articles: list[dict],
    credibility_scores: dict,
    agreement_scores: dict,
    missing_context: dict,
    contradiction_reports: list,
):
    """Fallback: assemble a TopicSummary without Gemini using raw article text."""
    # Use first article's content as headline / summary approximation
    first = articles[0]
    first_lines = [l.strip() for l in first["content"].splitlines() if l.strip()]
    title = first_lines[0][:120] if first_lines else "News Summary"
    standfirst = " ".join(first_lines[1:4]) if len(first_lines) > 1 else ""

    # Build a minimal Gemini-shaped dict from raw articles
    source_index = [{"article_id": a["article_id"], "source": a["source"]}
                    for a in articles]
    body_sections = [
        {
            "heading": a["source"],
            "content": "\n".join(
                [l.strip() for l in a["content"].splitlines() if l.strip()][:6]
            ),
            "citations": [
                {
                    "article_id": a["article_id"],
                    "source": a["source"],
                    "quote": (a["content"][:200].rsplit(" ", 1)[0] + "…"),
                    "bias_level": "neutral",
                }
            ],
        }
        for a in articles
    ]
    gemini_result = {
        "title": title,
        "standfirst": standfirst,
        "body_sections": body_sections,
        "source_index": source_index,
    }
    return _build_topic_summary(
        gemini_result, articles, credibility_scores,
        agreement_scores, missing_context, contradiction_reports,
    )


# ── Main pipeline function ────────────────────────────────────────────────────


def run_pipeline(articles_dir: str = ARTICLES_DIR) -> Optional[object]:
    """
    Execute the full pipeline and return a TopicSummary, or None on failure.
    Falls back to a Gemini-free summary if GEMINI_API_KEY is missing.
    """
    print(f"[pipeline] Starting pipeline on: {articles_dir}", flush=True)

    articles = _load_raw_articles(articles_dir)
    if not articles:
        print("[pipeline] No articles found — aborting.", flush=True)
        return None

    _run_sentiment(articles)
    agreement_scores, contradiction_reports, missing_context = _run_agreement(articles)
    credibility_scores = _run_credibility(
        articles, agreement_scores, contradiction_reports, missing_context
    )

    try:
        gemini_result = _run_gemini(articles)
        topic = _build_topic_summary(
            gemini_result, articles, credibility_scores,
            agreement_scores, missing_context, contradiction_reports,
        )
    except Exception as exc:
        print(f"[pipeline] Gemini unavailable ({exc}), building summary from raw text.", flush=True)
        topic = _build_topic_summary_without_gemini(
            articles, credibility_scores, agreement_scores,
            missing_context, contradiction_reports,
        )

    print(f"[pipeline] Done — slug: {topic.slug}", flush=True)
    return topic


# ── Background thread + cache ─────────────────────────────────────────────────


def _worker() -> None:
    global _topics
    with _lock:
        _status["running"] = True
        _status["error"] = None
    try:
        topic = run_pipeline()
        if topic:
            with _lock:
                _topics = [topic]
    except Exception as exc:
        print(f"[pipeline] ERROR: {exc}", flush=True)
        with _lock:
            _status["error"] = str(exc)
    finally:
        with _lock:
            _status["running"] = False
            _status["done"] = True


def start_background_pipeline() -> None:
    """Spawn a daemon thread that runs the full pipeline once."""
    t = threading.Thread(target=_worker, daemon=True, name="pipeline-worker")
    t.start()
    print("[pipeline] Background pipeline started.", flush=True)


def get_topics() -> list:
    """Return cached list[TopicSummary] (empty while pipeline is running)."""
    with _lock:
        return list(_topics)


def pipeline_status() -> dict:
    with _lock:
        return dict(_status)


# ── Standalone entry point ────────────────────────────────────────────────────


if __name__ == "__main__":
    import json
    import sys

    # Add project root to path so relative imports work when run directly
    sys.path.insert(0, os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..")))

    topic = run_pipeline()
    if topic:
        print(json.dumps(topic.model_dump(), indent=2, ensure_ascii=False, default=str))
