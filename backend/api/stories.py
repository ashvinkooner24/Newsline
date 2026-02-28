from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from ..models import StoryWrapper, User
from ..data.mockData import mock_stories, mock_users, add_story
from ..utils.slugify import slugify
from collections import defaultdict

router = APIRouter()


def _get_stories() -> list[StoryWrapper]:
    """
    Return stories from the pipeline cache when available,
    falling back to mock_stories (seeded from stories.json on startup).
    """
    try:
        from ..scoring.pipeline import get_cached_stories
        cached = get_cached_stories()
        if cached:
            return [StoryWrapper(**s) if isinstance(s, dict) else s for s in cached]
    except Exception:
        pass
    return mock_stories


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
    max_topics: int = 10              # max topic groups to process from CSVs


@router.post("/stories/ingest")
def ingest_story(req: IngestRequest):
    """
    Run the full scoring pipeline.
    - Provide articles_dir for legacy .txt mode (single topic).
    - Provide csv_dir for multi-topic mode (load CSVs, cluster, process).
    """
    try:
        from ..scoring.pipeline import run_pipeline
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Import error: {e}")

    if not req.articles_dir and not req.csv_dir:
        raise HTTPException(status_code=400, detail="Provide either articles_dir or csv_dir")

    try:
        results = run_pipeline(
            articles_dir=req.articles_dir,
            csv_dir=req.csv_dir,
            max_topics=req.max_topics,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    wrappers = []
    for result in results:
        wrapper = StoryWrapper(**result)
        wrappers.append(wrapper)

    # Update in-memory store so GET /stories returns the new data immediately
    from ..data.mockData import mock_stories
    mock_stories.clear()
    mock_stories.extend(wrappers)

    return wrappers


@router.get("/users", response_model=List[User])
def get_users():
    return mock_users

@router.get("/user/{username}", response_model=User)
def get_user(username: str):
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