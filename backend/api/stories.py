from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from ..models import StoryWrapper, User
from ..data.mockData import mock_users
from ..db import stories_collection, users_collection
from ..utils.slugify import slugify
from collections import defaultdict
import os

router = APIRouter()


# ---------------------------------------------------------------------------
# MongoDB helpers
# ---------------------------------------------------------------------------

def _save_stories_to_db(wrappers: list[StoryWrapper]) -> int:
    """Replace all documents in the stories collection with the given wrappers."""
    docs: list[dict] = []
    for w in wrappers:
        doc = w.model_dump()
        doc["_slug"] = w.story.slug or slugify(w.story.heading)
        docs.append(doc)

    # If MongoDB usage is disabled, skip writes (fast local mode)
    if os.getenv("MONGO_DISABLED", "true").lower() in ("1", "true", "yes"):
        print(f"[stories] MONGO_DISABLED set — skipping DB write, {len(docs)} docs not persisted")
        return 0

    # Try to persist to MongoDB but don't raise on failure — return 0 and
    # let the caller continue serving the results from memory/json.
    try:
        coll = stories_collection()
        coll.delete_many({})       # clear old stories
        if docs:
            coll.insert_many(docs)
        return len(docs)
    except Exception as exc:
        print(f"[stories] WARNING: Failed to save stories to MongoDB: {exc}")
        return 0


def _upsert_story_to_db(wrapper: StoryWrapper) -> None:
    """Insert or update a single story keyed by slug."""
    coll = stories_collection()
    slug = wrapper.story.slug or slugify(wrapper.story.heading)
    doc = wrapper.model_dump()
    doc["_slug"] = slug
    coll.replace_one({"_slug": slug}, doc, upsert=True)


def _get_stories() -> list[StoryWrapper]:
    """
    1. Try the pipeline in-memory cache (hot data from a running ingest).
    2. Fall back to MongoDB stories collection.
    3. Last resort: seed DB from stories.json if it exists.
    """
    # If explicitly disabled, skip MongoDB entirely and serve from stories.json
    if os.getenv("MONGO_DISABLED", "true").lower() in ("1", "true", "yes"):
        try:
            from ..data.mockData import _load_json_stories
            json_stories = _load_json_stories()
            if json_stories:
                print(f"[stories] MONGO_DISABLED set — serving {len(json_stories)} stories from stories.json")
                return json_stories
        except Exception:
            return []

    # 1. Pipeline cache
    try:
        from ..scoring.pipeline import get_cached_stories
        cached = get_cached_stories()
        if cached:
            return [StoryWrapper(**s) if isinstance(s, dict) else s for s in cached]
    except Exception:
        pass

    # 2. MongoDB
    try:
        coll = stories_collection()
        docs = list(coll.find({}, {"_id": 0}))
        if docs:
            return [StoryWrapper(**d) for d in docs]
    except Exception as exc:
        print(f"[stories] MongoDB read failed: {exc}")

    # 3. Seed from stories.json (one-time migration)
    try:
        from ..data.mockData import _load_json_stories
        json_stories = _load_json_stories()
        if json_stories:
            # Try to seed MongoDB, but don't fail if it's unreachable
            try:
                _save_stories_to_db(json_stories)
                print(f"[stories] Seeded {len(json_stories)} stories from stories.json → MongoDB")
            except Exception:
                print(f"[stories] Serving {len(json_stories)} stories from stories.json (MongoDB unavailable)")
            return json_stories
    except Exception:
        pass

    return []


@router.get("/pipeline/status")
def pipeline_status():
    """Surface the current state of the background scoring pipeline."""
    try:
        from ..scoring.pipeline import get_pipeline_status
        return get_pipeline_status()
    except Exception as exc:
        return {"state": "unavailable", "error": str(exc)}


@router.get("/stories", response_model=List[StoryWrapper])
def get_stories():
    return _get_stories()


@router.get("/stories/{slug}", response_model=StoryWrapper)
def get_story(slug: str):
    for story in _get_stories():
        story_slug = story.story.slug or slugify(story.story.heading)
        if story_slug == slug:
            return story
    raise HTTPException(status_code=404, detail="Story not found")


class IngestRequest(BaseModel):
    articles_dir: str | None = None   # directory of .txt files
    csv_dir: str | None = None        # directory of .csv files (e.g. "backend/scraping")
    max_topics: int = 300              # max topic groups to process from CSVs
    similarity_threshold: float | None = None
    min_group_size: int | None = None
    max_group_size: int | None = None
    min_sources: int | None = None


@router.post("/stories/ingest")
def ingest_story(req: IngestRequest):
    """
    Run the full scoring pipeline.
    - Provide articles_dir for legacy .txt mode (single topic).
    - Provide csv_dir for multi-topic mode (load CSVs, cluster, process).
    """
    import time
    import traceback

    try:
        from ..scoring.pipeline import run_pipeline
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Import error: {e}")

    if not req.articles_dir and not req.csv_dir:
        raise HTTPException(status_code=400, detail="Provide either articles_dir or csv_dir")

    t0 = time.time()
    print(f"\n{'='*60}")
    print(f"[ingest] Starting pipeline: csv_dir={req.csv_dir}, max_topics={req.max_topics}")
    print(f"{'='*60}")

    try:
        results = run_pipeline(
            articles_dir=req.articles_dir,
            csv_dir=req.csv_dir,
            max_topics=req.max_topics,
            similarity_threshold=req.similarity_threshold,
            min_group_size=req.min_group_size,
            max_group_size=req.max_group_size,
            min_sources=req.min_sources,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"[ingest] Pipeline finished in {elapsed:.1f}s ({elapsed/60:.1f} min) — {len(results)} stories")
    print(f"{'='*60}")

    wrappers = []
    for result in results:
        wrapper = StoryWrapper(**result)
        wrappers.append(wrapper)

    # Persist to MongoDB so GET /stories returns the new data immediately
    saved = _save_stories_to_db(wrappers)
    print(f"[ingest] Saved {saved} stories to MongoDB")

    return wrappers


@router.get("/users", response_model=List[User])
def get_users():
    try:
        coll = users_collection()
        docs = list(coll.find({}, {"_id": 0}))
        if docs:
            return [User(**d) for d in docs]
    except Exception:
        pass
    return mock_users


@router.get("/user/{username}", response_model=User)
def get_user(username: str):
    try:
        coll = users_collection()
        doc = coll.find_one({"username": username}, {"_id": 0})
        if doc:
            return User(**doc)
    except Exception:
        pass
    for user in mock_users:
        if user.username == username:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/sources")
def get_sources():
    """
    Build source profiles dynamically from the current story data.
    Returns a list of source profiles with article counts, credibility,
    bias, and the topics they've contributed to.
    """
    stories = _get_stories()

    # Accumulate stats per source name
    source_stats: dict[str, dict] = defaultdict(lambda: {
        "name": "",
        "bias_scores": [],
        "trust_scores": [],
        "article_count": 0,
        "topics": set(),
        "articles": [],
    })

    for wrapper in stories:
        story = wrapper.story
        category = story.category or 'General'

        # Gather provider-level info
        provider_map: dict[str, dict] = {}
        for provider in story.sources:
            provider_map[provider.name] = {
                "bias_score": provider.bias_score,
                "trust_score": provider.trust_score,
            }

        # Gather per-article info
        for article in story.articles:
            src_name = article.source
            stats = source_stats[src_name]
            stats["name"] = src_name
            stats["article_count"] += 1
            stats["topics"].add(category)
            stats["articles"].append({
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at,
            })
            # Use provider bias/trust if available
            if src_name in provider_map:
                stats["bias_scores"].append(provider_map[src_name]["bias_score"])
                stats["trust_scores"].append(provider_map[src_name]["trust_score"])

    results = []
    for src_name, stats in source_stats.items():
        avg_bias = (sum(stats["bias_scores"]) / len(stats["bias_scores"])) if stats["bias_scores"] else 0.0
        avg_trust = (sum(stats["trust_scores"]) / len(stats["trust_scores"])) if stats["trust_scores"] else 0.7
        sid = slugify(src_name)

        # Determine bias lean label
        if avg_bias < -0.6: bias_lean = "far-left"
        elif avg_bias < -0.3: bias_lean = "left"
        elif avg_bias < -0.1: bias_lean = "center-left"
        elif avg_bias <= 0.1: bias_lean = "center"
        elif avg_bias <= 0.3: bias_lean = "center-right"
        elif avg_bias <= 0.6: bias_lean = "right"
        else: bias_lean = "far-right"

        results.append({
            "source": {
                "id": sid,
                "name": src_name,
                "url": "#",
                "credibilityScore": round(avg_trust * 100),
                "biasLean": bias_lean,
                "country": "Unknown",
            },
            "totalArticles": stats["article_count"],
            "avgCredibility": round(avg_trust * 100),
            "biasHistory": [],
            "topTopics": sorted(stats["topics"]),
        })

    return results