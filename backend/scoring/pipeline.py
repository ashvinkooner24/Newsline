"""
scoring/pipeline.py

Orchestrates the full ML → Gemini pipeline and exposes a simple cache so the
FastAPI server can serve results immediately while a background thread runs.

Supports two modes:
  - articles_dir : all .txt files treated as one topic (legacy/test)
  - csv_dir      : load CSVs, cluster by topic, process each group

Usage (from main.py):
    from backend.scoring.pipeline import start_background_pipeline, get_cached_stories
"""

import json
import os
import re
import threading
from collections import defaultdict
from datetime import datetime

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
    "new york times":   0.80,
    "nytimes":          0.80,
    "cnn":              0.78,
    "associated press": 0.90,
    "ap":               0.90,
}

# Display names when the CSV filename is the only source hint
SOURCE_DISPLAY_NAMES: dict[str, str] = {
    "cnn": "CNN",
    "guardian": "The Guardian",
    "nytimes": "The New York Times",
    "bbc": "BBC News",
    "reuters": "Reuters",
    "ft": "Financial Times",
    "politico": "Politico",
    "aljazeera": "Al Jazeera",
    "ap": "Associated Press",
}

# Source names for legacy .txt test files
SOURCE_BY_FILENAME: dict[str, str] = {
    "neutral_1.txt": "The Guardian",
    "Neutral_2.txt": "Reuters",
    "obj_cred_1.txt": "BBC News",
    "obj_cred_2.txt": "Financial Times",
    "sub_fls.txt": "Al Jazeera",
    "sub_mc.txt": "Politico",
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
# Helper
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    t = text.lower()
    t = re.sub(r'[^a-z0-9]+', '-', t)
    return t.strip('-')


# ---------------------------------------------------------------------------
# Article loaders
# ---------------------------------------------------------------------------

def load_articles_from_txt(articles_dir: str) -> list[dict]:
    """Load .txt files from a directory. Each file = one article."""
    articles = []
    for filename in sorted(os.listdir(articles_dir)):
        if not filename.endswith('.txt'):
            continue
        path = os.path.join(articles_dir, filename)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read().strip()
        source = SOURCE_BY_FILENAME.get(filename, "Unknown")
        articles.append({
            "id": filename,
            "title": filename.replace('.txt', '').replace('_', ' ').title(),
            "text": text,
            "url": "#",
            "source": source,
            "published_at": datetime.utcnow().strftime("%Y-%m-%d"),
        })
    return articles


def load_articles_from_csv(csv_dir: str, max_per_source: int = 50) -> list[dict]:
    """Load articles from all CSV files in a directory."""
    import polars as pl

    all_articles = []
    for filename in sorted(os.listdir(csv_dir)):
        if not filename.endswith('.csv'):
            continue
        source_key = filename.replace('.csv', '').lower()
        source_name = SOURCE_DISPLAY_NAMES.get(source_key, source_key.title())
        filepath = os.path.join(csv_dir, filename)
        try:
            df = pl.read_csv(filepath)
        except Exception as e:
            print(f"[pipeline] Skipping {filename}: {e}")
            continue

        count = 0
        for row in df.iter_rows(named=True):
            if count >= max_per_source:
                break
            title = str(row.get("title", "")).strip()
            text = str(row.get("text", "")).strip()
            url = str(row.get("url", "#")).strip()
            if not text or len(text) < 100 or not title:
                continue
            article_id = _slugify(title)[:80] or f"{source_key}_{count}"
            all_articles.append({
                "id": article_id,
                "title": title,
                "text": text,
                "url": url,
                "source": source_name,
                "published_at": datetime.utcnow().strftime("%Y-%m-%d"),
            })
            count += 1

    return all_articles


# ---------------------------------------------------------------------------
# Topic grouping
# ---------------------------------------------------------------------------

def group_articles_by_topic(
    articles: list[dict],
    similarity_threshold: float = 0.55,
    min_group_size: int = 2,
    max_group_size: int = 8,
) -> list[list[dict]]:
    """
    Group articles by topic using sentence-transformer embeddings.
    Returns groups of 2+ articles from different sources about the same story.
    """
    from sentence_transformers import SentenceTransformer, util

    if len(articles) < 2:
        return [articles] if articles else []

    model = SentenceTransformer('all-MiniLM-L6-v2')
    titles = [a['title'] for a in articles]
    embeddings = model.encode(titles, convert_to_tensor=True)
    sim_matrix = util.cos_sim(embeddings, embeddings)

    assigned: set[int] = set()
    groups: list[list[dict]] = []

    for i in range(len(articles)):
        if i in assigned:
            continue
        group_indices = [i]
        assigned.add(i)
        group_sources = {articles[i]["source"]}

        for j in range(i + 1, len(articles)):
            if j in assigned or len(group_indices) >= max_group_size:
                continue
            avg_sim = sum(sim_matrix[k][j].item() for k in group_indices) / len(group_indices)
            if avg_sim >= similarity_threshold:
                group_indices.append(j)
                assigned.add(j)
                group_sources.add(articles[j]["source"])

        if len(group_indices) >= min_group_size and len(group_sources) >= 2:
            groups.append([articles[idx] for idx in group_indices])

    return groups


# ---------------------------------------------------------------------------
# Core pipeline for a single topic group
# ---------------------------------------------------------------------------

MAX_ARTICLE_CHARS = 4000  # truncate article text sent to scoring + Gemini
STORIES_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stories.json")


def _process_topic_group(articles: list[dict]) -> dict:
    """Run full scoring + Gemini aggregation for one topic group."""
    from .sentiment_scoring import score_article
    from .agreement_scoring import compute_agreement
    from .credibility_scoring import compute_article_credibility
    from .gemini_article_aggregator import (
        load_api_key,
        build_prompt,
        call_gemini,
        gemini_to_storywrapper,
    )

    # Attach reputation scores
    for art in articles:
        src_key = art.get("source", "").lower()
        art["reputation"] = SOURCE_REPUTATION.get(src_key, 0.5)

    # Sentiment scoring
    for art in articles:
        if "objectivity" not in art:
            truncated = art["text"][:MAX_ARTICLE_CHARS]
            obj, subj = score_article(truncated)
            art["objectivity"] = obj
            art["subjectivity"] = subj

    # Agreement scoring
    agreement_scores, contradiction_reports, missing_context = compute_agreement(articles)

    # Credibility scoring
    contradictions_per_article = defaultdict(list)
    for report in contradiction_reports:
        contradictions_per_article[report["wrong_article"]].append(report)

    credibility_scores: dict[str, float] = {}
    for art in articles:
        credibility_scores[art["id"]] = compute_article_credibility(
            art, agreement_scores, contradictions_per_article, missing_context,
        )

    provider_trust_map: dict[str, float] = {
        art["source"]: credibility_scores[art["id"]]
        for art in articles
        if art.get("source") and art["source"] != "unknown"
    }

    # Gemini aggregation
    api_key = load_api_key()
    gemini_articles = [
        {
            "article_id": art["id"],
            "source": art["source"],
            "content": art["text"][:MAX_ARTICLE_CHARS],
        }
        for art in articles
    ]
    prompt = build_prompt(gemini_articles)
    gemini_result = call_gemini(api_key, prompt)

    story_dict = gemini_to_storywrapper(
        gemini_result,
        credibility_scores=credibility_scores,
        provider_trust_map=provider_trust_map,
        article_metadata=articles,
    )

    return story_dict


def _save_stories(stories: list[dict], json_path: str = STORIES_JSON_PATH) -> None:
    """Write the full story list to disk, replacing existing content."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)
    print(f"[pipeline] Saved {len(stories)} stories → {json_path}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    articles_dir: str | None = None,
    csv_dir: str | None = None,
    max_topics: int = 10,
) -> list:
    """
    Full scoring pipeline.

    Modes:
      - articles_dir : legacy mode — all .txt files treated as one topic
      - csv_dir      : multi-topic mode — load CSVs, cluster by topic, process each
    """
    if csv_dir:
        all_articles = load_articles_from_csv(csv_dir)
        if not all_articles:
            raise FileNotFoundError(f"No usable articles found in CSV files in {csv_dir!r}")
        print(f"[pipeline] Loaded {len(all_articles)} articles from CSVs")

        topic_groups = group_articles_by_topic(all_articles)
        print(f"[pipeline] Found {len(topic_groups)} topic groups (processing up to {max_topics})")

    elif articles_dir:
        txt_articles = load_articles_from_txt(articles_dir)
        if not txt_articles:
            raise FileNotFoundError(f"No .txt files found in {articles_dir!r}")
        topic_groups = [txt_articles]

    else:
        raise ValueError("Provide either articles_dir or csv_dir")

    results = []
    for i, group in enumerate(topic_groups[:max_topics]):
        titles = [a["title"] for a in group]
        print(
            f"[pipeline] Processing topic {i + 1}/{min(len(topic_groups), max_topics)}: "
            f"{len(group)} articles — {titles[0][:60]}…"
        )
        try:
            story_dict = _process_topic_group(group)
            results.append(story_dict)
        except Exception as exc:
            print(f"[pipeline] ERROR on topic {i + 1}: {exc}")
            continue

    _save_stories(results)
    return results


# ---------------------------------------------------------------------------
# Background thread management
# ---------------------------------------------------------------------------

def _pipeline_worker(
    articles_dir: str | None,
    csv_dir: str | None,
    max_topics: int,
) -> None:
    global _stories_cache, _status
    try:
        with _lock:
            _status = {"state": "running", "error": None}
        print("[pipeline] Starting pipeline…")
        results = run_pipeline(
            articles_dir=articles_dir, csv_dir=csv_dir, max_topics=max_topics,
        )
        with _lock:
            _stories_cache = results
            _status = {"state": "done", "error": None}
        print(f"[pipeline] Done — {len(results)} story/stories cached.")
    except Exception as exc:
        with _lock:
            _status = {"state": "error", "error": str(exc)}
        print(f"[pipeline] ERROR: {exc}")


def start_background_pipeline(
    articles_dir: str | None = None,
    csv_dir: str | None = None,
    max_topics: int = 10,
) -> None:
    """
    Spawn a daemon thread that runs the full pipeline.
    Results are stored in the module-level cache and retrievable via
    get_cached_stories().
    """
    if articles_dir is None and csv_dir is None:
        articles_dir = os.path.join(os.path.dirname(__file__), "test")

    thread = threading.Thread(
        target=_pipeline_worker,
        args=(articles_dir, csv_dir, max_topics),
        daemon=True,
        name="scoring-pipeline",
    )
    thread.start()


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--csv":
        csv_dir = (
            sys.argv[2] if len(sys.argv) > 2
            else os.path.join(os.path.dirname(__file__), "..", "scraping")
        )
        max_topics = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        print(f"[pipeline] CSV mode: {csv_dir}, max_topics={max_topics}")
        results = run_pipeline(csv_dir=csv_dir, max_topics=max_topics)
    else:
        articles_dir = (
            sys.argv[1] if len(sys.argv) > 1
            else os.path.join(os.path.dirname(__file__), "test")
        )
        print(f"[pipeline] TXT mode: {articles_dir}")
        results = run_pipeline(articles_dir=articles_dir)

    print(f"[pipeline] Complete — {len(results)} story/stories produced.")
