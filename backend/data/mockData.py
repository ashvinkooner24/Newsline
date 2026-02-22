"""
Mock / seed data for the API.

Loading order
-------------
1. Try ``generatedTopics.json`` at the project root (real Gemini output).
   The file uses **camelCase** (frontend convention), so keys are converted
   to **snake_case** before being parsed into Pydantic models.
2. If the file is missing or cannot be parsed, fall back to inline mock data
   that exercises every field the frontend expects.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from ..models import TopicSummary, UserProfile

# ── camelCase → snake_case key converter ─────────────────────────────────────

_RE1 = re.compile(r"(.)([A-Z][a-z]+)")
_RE2 = re.compile(r"([a-z0-9])([A-Z])")


def _camel_to_snake(name: str) -> str:
    s = _RE1.sub(r"\1_\2", name)
    return _RE2.sub(r"\1_\2", s).lower()


def _convert_keys(obj: Any) -> Any:
    """Recursively convert all dict keys from camelCase to snake_case."""
    if isinstance(obj, dict):
        return {_camel_to_snake(k): _convert_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_keys(item) for item in obj]
    return obj


# ── Load generatedTopics.json ────────────────────────────────────────────────

def _load_generated_topics() -> list[TopicSummary]:
    json_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "generatedTopics.json")
    )
    if not os.path.isfile(json_path):
        return []
    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        snake_data = _convert_keys(data)
        return [TopicSummary(**item) for item in snake_data]
    except Exception as exc:
        print(f"[mockData] Failed to load generatedTopics.json: {exc}")
        return []


generated_topics = _load_generated_topics()

# ── Inline fallback topics ───────────────────────────────────────────────────

_FALLBACK_RAW: list[dict] = [
    {
        "id": "climate-change-policy-updates",
        "topic": "Climate Change Policy Updates",
        "slug": "climate-change-policy-updates",
        "headline": "Governments Worldwide Update Climate Policies Amid Rising Pressure",
        "summary": "Multiple nations are revising climate policies as global temperatures rise, with sources divided on the effectiveness of new measures.",
        "sections": [
            {
                "heading": "Policy Consensus Among Mainstream Sources",
                "content": "Governments worldwide are updating climate policies in response to mounting evidence of accelerating climate change. The EU, US, and China have each proposed new frameworks.",
                "citations": [
                    {"article_id": "art-guardian-1", "text": "The EU has finalized its updated climate action plan, targeting 55 % emissions reduction by 2030.", "bias_level": "neutral"},
                    {"article_id": "art-bbc-1", "text": "BBC analysis confirms broad consensus among scientists on the urgency of policy updates.", "bias_level": "neutral"},
                ],
                "stats": {"bias_lean": "center", "lean_score": 5, "credibility_score": 93, "source_count": 2, "agreement": 90},
            },
            {
                "heading": "Skepticism from Right-Leaning Outlets",
                "content": "Some sources question the effectiveness and economic impact of new climate measures, calling for a more measured approach.",
                "citations": [
                    {"article_id": "art-fox-1", "text": "The rush to green energy threatens millions of jobs in traditional energy sectors.", "bias_level": "right"},
                ],
                "stats": {"bias_lean": "right", "lean_score": 70, "credibility_score": 70, "source_count": 1, "agreement": 40},
            },
        ],
        "articles": [
            {
                "id": "art-guardian-1",
                "title": "The Guardian: EU Finalizes Climate Action Plan",
                "url": "#",
                "source": {"id": "guardian", "name": "The Guardian", "url": "https://theguardian.com", "credibility_score": 82, "bias_lean": "center-left", "country": "UK"},
                "published_at": "2026-02-20",
                "excerpt": "The EU has set ambitious targets for emissions reduction.",
                "tone": "analytical",
                "tone_score": {"emotional": 20, "logical": 80},
                "fact_check": {"verdict": "verified", "details": "Claims match EU official documents.", "missing_context": []},
            },
            {
                "id": "art-bbc-1",
                "title": "BBC: Global Climate Policy Overview",
                "url": "#",
                "source": {"id": "bbc", "name": "BBC", "url": "https://bbc.com", "credibility_score": 88, "bias_lean": "center", "country": "UK"},
                "published_at": "2026-02-19",
                "excerpt": "An overview of climate policy changes across major economies.",
                "tone": "balanced",
                "tone_score": {"emotional": 15, "logical": 85},
                "fact_check": {"verdict": "verified", "details": "Neutral reporting of confirmed data.", "missing_context": []},
            },
            {
                "id": "art-fox-1",
                "title": "Fox News: Climate Push Threatens Energy Jobs",
                "url": "#",
                "source": {"id": "foxnews", "name": "Fox News", "url": "https://foxnews.com", "credibility_score": 62, "bias_lean": "right", "country": "US"},
                "published_at": "2026-02-18",
                "excerpt": "Critics warn aggressive climate targets could harm workers.",
                "tone": "emotional",
                "tone_score": {"emotional": 65, "logical": 35},
                "fact_check": {"verdict": "mixed", "details": "Job-loss estimates sourced from industry-funded study.", "missing_context": ["Does not mention job creation in renewables."]},
            },
        ],
        "bias_analysis": {"overall_lean": "center", "lean_score": 10, "left_source_count": 1, "center_source_count": 1, "right_source_count": 1},
        "credibility": {"score": 82, "article_count": 3, "avg_source_credibility": 77, "source_agreement": 65, "label": "High"},
        "updated_at": "2026-02-21T10:30:00Z",
        "category": "Environment",
        "country": "Global",
        "subtopic": "Climate Change",
        "is_featured": True,
        "comments": [],
        "community_notes": [],
    },
    {
        "id": "tech-regulation-in-2026",
        "topic": "Tech Regulation in 2026",
        "slug": "tech-regulation-in-2026",
        "headline": "New Laws Target Big Tech Companies Amid Privacy and Antitrust Concerns",
        "summary": "Governments are introducing sweeping regulations aimed at technology giants, sparking debate between privacy advocates and industry groups.",
        "sections": [
            {
                "heading": "New Privacy and Antitrust Legislation",
                "content": "New laws are targeting big tech companies with stricter data privacy and antitrust requirements, expanding the EU Digital Markets Act approach worldwide.",
                "citations": [
                    {"article_id": "art-guardian-2", "text": "EU regulators have opened new investigations into data practices of major tech firms.", "bias_level": "neutral"},
                    {"article_id": "art-fox-2", "text": "Industry leaders warn regulation could stifle innovation and American competitiveness.", "bias_level": "right"},
                ],
                "stats": {"bias_lean": "center", "lean_score": 20, "credibility_score": 80, "source_count": 2, "agreement": 55},
            },
            {
                "heading": "Industry Pushback",
                "content": "Industry groups are lobbying intensely for less regulation, arguing that market forces should prevail.",
                "citations": [
                    {"article_id": "art-fox-2", "text": "Tech executives unanimously oppose what they call government overreach.", "bias_level": "right"},
                ],
                "stats": {"bias_lean": "right", "lean_score": 70, "credibility_score": 75, "source_count": 1, "agreement": 35},
            },
        ],
        "articles": [
            {
                "id": "art-guardian-2",
                "title": "The Guardian: EU Opens New Tech Investigations",
                "url": "#",
                "source": {"id": "guardian", "name": "The Guardian", "url": "https://theguardian.com", "credibility_score": 82, "bias_lean": "center-left", "country": "UK"},
                "published_at": "2026-02-18",
                "excerpt": "EU regulators are expanding their scrutiny of big tech.",
                "tone": "analytical",
                "tone_score": {"emotional": 25, "logical": 75},
                "fact_check": {"verdict": "verified", "details": "Based on official EU statements.", "missing_context": []},
            },
            {
                "id": "art-fox-2",
                "title": "Fox News: Regulation Threatens Innovation",
                "url": "#",
                "source": {"id": "foxnews", "name": "Fox News", "url": "https://foxnews.com", "credibility_score": 62, "bias_lean": "right", "country": "US"},
                "published_at": "2026-02-17",
                "excerpt": "Industry groups push back against new regulations.",
                "tone": "emotional",
                "tone_score": {"emotional": 70, "logical": 30},
                "fact_check": {"verdict": "mixed", "details": "Valid concerns mixed with unsupported claims.", "missing_context": ["Omits bipartisan support for some regulation."]},
            },
        ],
        "bias_analysis": {"overall_lean": "center-right", "lean_score": 30, "left_source_count": 1, "center_source_count": 0, "right_source_count": 1},
        "credibility": {"score": 78, "article_count": 2, "avg_source_credibility": 72, "source_agreement": 50, "label": "Medium"},
        "updated_at": "2026-02-19T09:00:00Z",
        "category": "Technology",
        "country": "Global",
        "subtopic": "Tech Regulation",
        "comments": [],
        "community_notes": [],
    },
    {
        "id": "economic-recovery-post-pandemic",
        "topic": "Economic Recovery Post-Pandemic",
        "slug": "economic-recovery-post-pandemic",
        "headline": "Global Economies Show Signs of Recovery as Stimulus Debate Continues",
        "summary": "Economic indicators point to a broad recovery, but experts remain divided on the role of government stimulus versus market-driven growth.",
        "sections": [
            {
                "heading": "Recovery Indicators",
                "content": "Global GDP growth has returned to pre-pandemic levels in most advanced economies, with unemployment falling and consumer spending rebounding strongly.",
                "citations": [
                    {"article_id": "art-bbc-2", "text": "OECD data confirms GDP growth returned to 2019 levels across G7 nations.", "bias_level": "neutral"},
                    {"article_id": "art-reuters-1", "text": "Unemployment in the US has fallen below 4 % for the first time since 2020.", "bias_level": "neutral"},
                ],
                "stats": {"bias_lean": "center", "lean_score": 0, "credibility_score": 91, "source_count": 2, "agreement": 88},
            },
            {
                "heading": "Stimulus Effectiveness Debate",
                "content": "Debate continues on whether government stimulus drove the recovery or merely created inflation, with progressive and conservative outlets offering sharply different interpretations.",
                "citations": [
                    {"article_id": "art-guardian-3", "text": "Government spending was the primary driver of recovery according to Keynesian economists.", "bias_level": "left"},
                    {"article_id": "art-fox-3", "text": "Stimulus spending fueled inflation that wiped out gains for working families.", "bias_level": "right"},
                ],
                "stats": {"bias_lean": "center", "lean_score": 5, "credibility_score": 72, "source_count": 2, "agreement": 35},
            },
        ],
        "articles": [
            {
                "id": "art-bbc-2",
                "title": "BBC: Global GDP Returns to Pre-Pandemic Levels",
                "url": "#",
                "source": {"id": "bbc", "name": "BBC", "url": "https://bbc.com", "credibility_score": 88, "bias_lean": "center", "country": "UK"},
                "published_at": "2026-02-17",
                "excerpt": "Economic data confirms recovery across major economies.",
                "tone": "analytical",
                "tone_score": {"emotional": 15, "logical": 85},
                "fact_check": {"verdict": "verified", "details": "OECD data accurately cited.", "missing_context": []},
            },
            {
                "id": "art-reuters-1",
                "title": "Reuters: US Unemployment Falls Below 4 %",
                "url": "#",
                "source": {"id": "reuters", "name": "Reuters", "url": "https://reuters.com", "credibility_score": 92, "bias_lean": "center", "country": "UK"},
                "published_at": "2026-02-16",
                "excerpt": "Labour market data points to continued recovery.",
                "tone": "balanced",
                "tone_score": {"emotional": 10, "logical": 90},
                "fact_check": {"verdict": "verified", "details": "BLS data correctly reported.", "missing_context": []},
            },
            {
                "id": "art-guardian-3",
                "title": "The Guardian: Stimulus Spending Drove Recovery",
                "url": "#",
                "source": {"id": "guardian", "name": "The Guardian", "url": "https://theguardian.com", "credibility_score": 82, "bias_lean": "center-left", "country": "UK"},
                "published_at": "2026-02-15",
                "excerpt": "Economic analysis supports role of fiscal stimulus.",
                "tone": "analytical",
                "tone_score": {"emotional": 30, "logical": 70},
                "fact_check": {"verdict": "mostly-true", "details": "Valid argument but omits monetary policy factors.", "missing_context": ["Central bank rate cuts also contributed."]},
            },
            {
                "id": "art-fox-3",
                "title": "Fox News: Stimulus Created Inflation, Not Growth",
                "url": "#",
                "source": {"id": "foxnews", "name": "Fox News", "url": "https://foxnews.com", "credibility_score": 62, "bias_lean": "right", "country": "US"},
                "published_at": "2026-02-14",
                "excerpt": "Critics argue stimulus spending fueled damaging inflation.",
                "tone": "emotional",
                "tone_score": {"emotional": 60, "logical": 40},
                "fact_check": {"verdict": "mixed", "details": "Inflation link is debated; impact overstated.", "missing_context": ["Supply-chain disruptions also drove inflation."]},
            },
        ],
        "bias_analysis": {"overall_lean": "center", "lean_score": -5, "left_source_count": 1, "center_source_count": 2, "right_source_count": 1},
        "credibility": {"score": 80, "article_count": 4, "avg_source_credibility": 81, "source_agreement": 58, "label": "High"},
        "updated_at": "2026-02-18T14:00:00Z",
        "category": "Economy",
        "country": "Global",
        "subtopic": "Recovery",
        "is_featured": True,
        "comments": [],
        "community_notes": [],
    },
]

_fallback_topics = [TopicSummary(**t) for t in _FALLBACK_RAW]

# ── Exported data ────────────────────────────────────────────────────────────

mock_topics: list[TopicSummary] = generated_topics if generated_topics else _fallback_topics

mock_users: list[UserProfile] = [
    UserProfile(id="u1", name="DataDrivenReader", joined_at="2025-06-15", articles_read=342, comments_count=28, bias_lean="center", lean_score=-3, reputation=87, is_public=True),
    UserProfile(id="u2", name="SkepticalObserver", joined_at="2025-09-01", articles_read=198, comments_count=45, bias_lean="center-left", lean_score=-15, reputation=72, is_public=True),
    UserProfile(id="u3", name="MediaAnalyst", joined_at="2025-03-20", articles_read=567, comments_count=89, bias_lean="center", lean_score=2, reputation=91, is_public=True),
    UserProfile(id="u4", name="NewsJunkie42", joined_at="2025-11-10", articles_read=112, comments_count=12, bias_lean="center-right", lean_score=18, reputation=65, is_public=False),
    UserProfile(id="u5", name="FactChecker101", joined_at="2025-01-05", articles_read=890, comments_count=156, bias_lean="center", lean_score=-1, reputation=95, is_public=True),
]
