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
import time
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
    "usa today":        0.72,
    "fox news":         0.68,
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
    "usa_today": "USA Today",
    "usatoday": "USA Today",
    "fox_news": "Fox News",
    "foxnews": "Fox News",
}


def _normalise_source_key(filename: str) -> str:
    """Turn a CSV filename into a canonical source key.

    Strips trailing digits/underscores so that e.g.
      USA_Today02_1-5.csv  →  usa_today
      Fox_News.csv         →  fox_news
    """
    key = filename.replace('.csv', '').lower()
    # Strip trailing version / batch suffixes like '02_1-5'
    key = re.sub(r'[\d_-]+$', '', key).rstrip('_')
    return key or filename.replace('.csv', '').lower()

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


_DATE_FROM_URL = re.compile(r'/(20\d{2})/(\d{2})/(\d{2})/')
_DATE_MONTH_NAME = re.compile(
    r'/(20\d{2})/(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?'
    r'|july?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)/(\d{1,2})',
    re.IGNORECASE,
)
_MONTH_MAP = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12",
}


def _extract_date_from_url(url: str) -> str | None:
    """Try to extract a YYYY-MM-DD date from a URL path."""
    m = _DATE_FROM_URL.search(url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = _DATE_MONTH_NAME.search(url)
    if m:
        month_num = _MONTH_MAP.get(m.group(2).lower())
        if month_num:
            return f"{m.group(1)}-{month_num}-{int(m.group(3)):02d}"
    return None


# URL path segments that indicate non-news content (shopping, deals, lifestyle, etc.)
_NON_NEWS_URL_SEGMENTS = {
    'deals', 'shopping', 'lifestyle', 'food-drink', 'food', 'travel',
    'pets-animals', 'cars', 'graphics', 'nletter', 'weather',
    'opinion', 'video', 'videos', 'live-story', 'sitemap',
}

# Titles that should be skipped outright
_SKIP_TITLES = {
    'sitemap', 'index', '', 'help center', 'unsupported eu page',
    'accessibility support', 'site index', 'usa today',
}


def load_articles_from_csv(csv_dir: str, max_per_source: int = 50) -> list[dict]:
    """Load articles from all CSV files in a directory.

    - Normalises source keys so multiple CSVs from the same outlet
      (e.g. USA_Today.csv and USA_Today02_1-5.csv) map to one source.
    - Filters out non-news content (shopping, deals, opinion, etc.).
    - Deduplicates articles by title within each source.
    """
    import polars as pl

    all_articles: list[dict] = []
    seen_titles: dict[str, set[str]] = defaultdict(set)  # source -> set of lower titles
    csv_files = sorted(f for f in os.listdir(csv_dir) if f.endswith('.csv'))
    print(f"[pipeline] Found {len(csv_files)} CSV files in {csv_dir}")
    for filename in csv_files:
        source_key = _normalise_source_key(filename)
        source_name = SOURCE_DISPLAY_NAMES.get(source_key, source_key.replace('_', ' ').title())
        filepath = os.path.join(csv_dir, filename)
        try:
            t0 = time.time()
            df = pl.read_csv(filepath)
            print(f"[pipeline]   {filename}: {len(df)} rows loaded in {time.time()-t0:.1f}s  (source_key={source_key!r} → {source_name!r})")
        except Exception as e:
            print(f"[pipeline]   Skipping {filename}: {e}")
            continue

        count = 0
        skipped_nonnews = 0
        skipped_dupe = 0
        for row in df.iter_rows(named=True):
            if count >= max_per_source:
                break
            title = str(row.get("title", "")).strip()
            text = str(row.get("text", "")).strip()
            url = str(row.get("url", "#")).strip()
            if not text or len(text) < 100 or not title:
                continue
            # Skip junk titles
            if title.lower() in _SKIP_TITLES:
                continue
            # Skip non-news URL categories
            url_lower = url.lower()
            if any(f'/{seg}/' in url_lower or url_lower.endswith(f'/{seg}') for seg in _NON_NEWS_URL_SEGMENTS):
                skipped_nonnews += 1
                continue
            # Deduplicate by title within this source
            title_key = title.lower().strip()
            if title_key in seen_titles[source_name]:
                skipped_dupe += 1
                continue
            seen_titles[source_name].add(title_key)

            article_id = _slugify(title)[:80] or f"{source_key}_{count}"
            published_at = _extract_date_from_url(url) or datetime.utcnow().strftime("%Y-%m-%d")
            all_articles.append({
                "id": article_id,
                "title": title,
                "text": text,
                "url": url,
                "source": source_name,
                "published_at": published_at,
            })
            count += 1

        print(f"[pipeline]   {filename}: kept {count} articles, "
              f"skipped {skipped_dupe} dupes + {skipped_nonnews} non-news (source={source_name})")

    # Final cross-source dedup: if exact same title appears under two sources, keep both
    # (that's actually desired — same story, different outlets)
    print(f"[pipeline] Total: {len(all_articles)} unique articles from {len(set(a['source'] for a in all_articles))} sources")
    return all_articles


# ---------------------------------------------------------------------------
# Topic grouping
# ---------------------------------------------------------------------------

def group_articles_by_topic(
    articles: list[dict],
    similarity_threshold: float = 0.62,
    min_group_size: int = 2,
    max_group_size: int = 12,
) -> list[list[dict]]:
    """
    Group articles by topic using sentence-transformer embeddings.
    Returns groups of 2+ articles from different sources about the same story.
    Uses title + first 200 chars of body for richer semantic matching.
    """
    from sentence_transformers import SentenceTransformer, util

    if len(articles) < 2:
        return [articles] if articles else []

    print(f"[pipeline] Topic grouping: encoding {len(articles)} articles (title+lead)…")
    t0 = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    texts = [a['title'] + '. ' + a.get('text', '')[:200] for a in articles]
    embeddings = model.encode(texts, convert_to_tensor=True)
    sim_matrix = util.cos_sim(embeddings, embeddings)
    print(f"[pipeline] Topic grouping: embedding + similarity done in {time.time()-t0:.1f}s")

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
            group = [articles[idx] for idx in group_indices]
            # Final check: deduplicate articles within the group by title
            seen = set()
            deduped = []
            for a in group:
                tkey = a['title'].lower().strip()
                if tkey not in seen:
                    seen.add(tkey)
                    deduped.append(a)
            group = deduped
            grp_sources = sorted({a['source'] for a in group})
            # After dedup, re-check we still have 2+ sources
            if len(grp_sources) < 2:
                continue
            groups.append(group)
            print(f"[pipeline]   Group #{len(groups)}: {len(group)} articles from {grp_sources}")
            for a in group:
                print(f"[pipeline]     • [{a['source']}] {a['title'][:70]}")

    print(f"[pipeline] Topic grouping: {len(groups)} groups formed, "
          f"{len(assigned)}/{len(articles)} articles assigned")
    return groups


# ---------------------------------------------------------------------------
# Core pipeline for a single topic group
# ---------------------------------------------------------------------------

MAX_ARTICLE_CHARS = 4000  # truncate article text sent to scoring + Gemini
STORIES_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stories.json")

# Keywords in title / URL that indicate a sports story
_SPORTS_KEYWORDS = re.compile(
    r'\b(olympic|olympics|medal|nfl|nba|mlb|nhl|nascar|wnba|ncaa|fifa|'
    r'world cup|premier league|la liga|serie a|bundesliga|'
    r'touchdown|quarterback|home run|slam dunk|goal scored|'
    r'batting|cricket|t20|ipl|rugby|tennis|golf|'
    r'playoff|super bowl|championship|tournament|match|game\s+\d|'
    r'draft|mock draft|spring training|preseason|postseason|'
    r'coach|roster|trade|free agent|mvp|'
    r'soccer|football|basketball|baseball|hockey|boxing|mma|ufc)\b',
    re.IGNORECASE,
)


def _is_sports_topic(articles: list[dict]) -> bool:
    """Return True if the majority of articles in this group are about sports."""
    sports_count = 0
    for a in articles:
        text_to_check = a.get('title', '') + ' ' + a.get('url', '')
        if _SPORTS_KEYWORDS.search(text_to_check):
            sports_count += 1
    return sports_count >= len(articles) * 0.5


def _process_topic_group(articles: list[dict]) -> dict:
    """Run full scoring + Gemini aggregation for one topic group."""
    from .sentiment_scoring import score_article
    from .agreement_scoring import compute_agreement
    from .credibility_scoring import compute_article_credibility
    from .gemini_article_aggregator import (
        load_api_key,
        build_prompt,
        call_gemini,
        call_llm,
        gemini_to_storywrapper,
    )

    group_t0 = time.time()
    n = len(articles)
    src_list = ", ".join(sorted({a['source'] for a in articles}))
    print(f"[pipeline]   ── Step 0: {n} articles from [{src_list}]")

    # Attach reputation scores
    for art in articles:
        src_key = art.get("source", "").lower()
        art["reputation"] = SOURCE_REPUTATION.get(src_key, 0.65)
        print(f"[pipeline]     #{articles.index(art)+1} [{art['source']}] rep={art['reputation']:.2f} "
              f"| {art['title'][:60]}")

    # ── STEP 1: Sentiment scoring ──
    t0 = time.time()
    print(f"[pipeline]   ── Step 1/4: Sentiment scoring ({n} articles)…")
    for idx, art in enumerate(articles):
        if "objectivity" not in art:
            truncated = art["text"][:MAX_ARTICLE_CHARS]
            sent_count = len(truncated.split('. '))
            art_t0 = time.time()
            obj, subj = score_article(truncated)
            art["objectivity"] = obj
            art["subjectivity"] = subj
            print(f"[pipeline]     sentiment {idx+1}/{n}: obj={obj:.3f} subj={subj:.3f} "
                  f"(~{sent_count} sentences, {time.time()-art_t0:.1f}s) "
                  f"[{art['source']}: {art['title'][:50]}…]")
    print(f"[pipeline]   ── Step 1 DONE in {time.time()-t0:.1f}s")

    # ── STEP 2: Agreement scoring ──
    unique_sources = {a.get("source", "") for a in articles}
    is_sports = _is_sports_topic(articles)
    skip_agreement = is_sports or len(unique_sources) < 3
    if is_sports:
        print(f"[pipeline]   ⚽ Sports topic detected — skipping agreement scoring entirely")
    elif len(unique_sources) < 3:
        print(f"[pipeline]   ⚡ Only {len(unique_sources)} source(s) — skipping agreement scoring")
    t0 = time.time()
    print(f"[pipeline]   ── Step 2/4: Agreement scoring ({n} articles)…")
    agreement_scores, contradiction_reports, missing_context = compute_agreement(
        articles, skip_contradictions=skip_agreement,
    )
    print(f"[pipeline]   ── Step 2 DONE in {time.time()-t0:.1f}s — "
          f"{len(contradiction_reports)} contradictions, "
          f"{sum(len(v) for v in missing_context.values()) if isinstance(missing_context, dict) else 0} missing claims")

    # ── STEP 3: Credibility scoring ──
    t0 = time.time()
    print(f"[pipeline]   ── Step 3/4: Credibility scoring…")
    contradictions_per_article = defaultdict(list)
    for report in contradiction_reports:
        contradictions_per_article[report["wrong_article"]].append(report)

    credibility_scores: dict[str, float] = {}
    for art in articles:
        credibility_scores[art["id"]] = compute_article_credibility(
            art, agreement_scores, contradictions_per_article, missing_context,
        )
    print(f"[pipeline]   ── Step 3 DONE in {time.time()-t0:.1f}s")

    provider_trust_map: dict[str, float] = {
        art["source"]: credibility_scores[art["id"]]
        for art in articles
        if art.get("source") and art["source"] != "unknown"
    }

    # ── STEP 4: LLM aggregation (Gemini or Azure OpenAI) ──
    t0 = time.time()
    print(f"[pipeline]   ── Step 4/4: LLM API call…")
    llm_articles = [
        {
            "article_id": art["id"],
            "source": art["source"],
            "content": art["text"][:MAX_ARTICLE_CHARS],
        }
        for art in articles
    ]
    prompt = build_prompt(llm_articles)
    total_chars = sum(len(a["content"]) for a in llm_articles)
    print(f"[pipeline]     Sending {len(llm_articles)} articles ({total_chars:,} chars) to LLM…")
    gemini_result = call_llm(prompt)
    print(f"[pipeline]   ── Step 4 DONE in {time.time()-t0:.1f}s")

    story_dict = gemini_to_storywrapper(
        gemini_result,
        credibility_scores=credibility_scores,
        provider_trust_map=provider_trust_map,
        article_metadata=articles,
        agreement_scores=agreement_scores,
        contradiction_reports=contradiction_reports,
        missing_context=missing_context,
    )

    elapsed = time.time() - group_t0
    print(f"[pipeline]   ✓ Topic group complete in {elapsed:.1f}s")
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
        t_load = time.time()
        all_articles = load_articles_from_csv(csv_dir)
        if not all_articles:
            raise FileNotFoundError(f"No usable articles found in CSV files in {csv_dir!r}")
        print(f"[pipeline] Loaded {len(all_articles)} articles from CSVs in {time.time()-t_load:.1f}s")

        t_group = time.time()
        topic_groups = group_articles_by_topic(all_articles)
        print(f"[pipeline] Found {len(topic_groups)} topic groups in {time.time()-t_group:.1f}s "
              f"(processing up to {max_topics})")

    elif articles_dir:
        txt_articles = load_articles_from_txt(articles_dir)
        if not txt_articles:
            raise FileNotFoundError(f"No .txt files found in {articles_dir!r}")
        topic_groups = [txt_articles]

    else:
        raise ValueError("Provide either articles_dir or csv_dir")

    results = []
    pipeline_t0 = time.time()
    for i, group in enumerate(topic_groups[:max_topics]):
        titles = [a["title"] for a in group]
        sources = sorted({a["source"] for a in group})
        print(
            f"\n[pipeline] ═══════════════════════════════════════════════"
            f"\n[pipeline] Topic {i + 1}/{min(len(topic_groups), max_topics)}: "
            f"{len(group)} articles from {len(sources)} sources"
            f"\n[pipeline]   Title: {titles[0][:80]}…"
            f"\n[pipeline] ═══════════════════════════════════════════════"
        )
        try:
            story_dict = _process_topic_group(group)
            results.append(story_dict)
        except Exception as exc:
            import traceback
            print(f"[pipeline] ERROR on topic {i + 1}: {exc}")
            traceback.print_exc()
            continue

    total_elapsed = time.time() - pipeline_t0
    print(f"\n[pipeline] ═══════════════════════════════════════════════")
    print(f"[pipeline] ALL TOPICS DONE: {len(results)}/{min(len(topic_groups), max_topics)} "
          f"succeeded in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"[pipeline] ═══════════════════════════════════════════════")

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
