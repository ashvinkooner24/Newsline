import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Directory containing this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Default articles folder is the "test" folder next to this script
DEFAULT_ARTICLES_DIR = os.path.join(SCRIPT_DIR, "test")

MODEL_NAME = "gemini-3-flash-preview"

SOURCE_BY_FILENAME = {
    "neutral_1.txt": "The Guardian",
    "Neutral_2.txt": "Reuters",
    "obj_cred_1.txt": "BBC News",
    "obj_cred_2.txt": "Financial Times",
    "sub_fls.txt": "Al Jazeera",
    "sub_mc.txt": "Politico",
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "standfirst": {"type": "string"},
        "body_sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"},
                    "content": {"type": "string"},
                    "citations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "article_id": {"type": "string"},
                                "quote": {"type": "string"},
                                "bias_level": {"type": "string"},
                            },
                            "required": ["source", "article_id", "quote", "bias_level"],
                        },
                    },
                },
                "required": ["heading", "content", "citations"],
            },
        },
        "source_index": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "article_id": {"type": "string"},
                },
                "required": ["source", "article_id"],
            },
        },
    },
    "required": ["title", "standfirst", "body_sections", "source_index"],
}


def load_api_key():
    # Look for .env at the project root (3 levels up from this script)
    env_path = os.path.join(SCRIPT_DIR, "..", "..", ".env")
    load_dotenv(env_path)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")
    return api_key


def load_articles(articles_dir):
    if not os.path.isdir(articles_dir):
        raise FileNotFoundError(f"Articles folder not found: {articles_dir}")

    files = sorted(f for f in os.listdir(articles_dir) if f.endswith(".txt"))
    if not files:
        raise RuntimeError(f"No .txt files found in: {articles_dir}")

    articles = []
    for filename in files:
        filepath = os.path.join(articles_dir, filename)
        source = SOURCE_BY_FILENAME.get(filename, f"Unknown ({filename})")
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        articles.append({"article_id": filename, "source": source, "content": content})

    return articles


def build_prompt(articles):
    return {
        "task": "Create one consolidated news article from multiple source articles.",
        "style_rules": [
            "Use objective, factual, unemotional language.",
            "Avoid sensational, clickbait, or persuasive framing.",
            "Do not invent facts not present in the provided sources.",
            "If sources differ, present differences neutrally and cite the relevant sources.",
        ],
        "input_articles": articles,
        "output_requirements": {
            "title": "Create a neutral article title based on source material.",
            "standfirst": "Write a concise summary paragraph.",
            "body_sections": (
                "Split the body into thematic sections. "
                "Each section must have a 'citations' array of objects. "
                "Each citation must contain: "
                "'source' (the outlet name), "
                "'article_id' (the article's article_id from input), "
                "'quote' (a short verbatim or near-verbatim extract from that source's text that directly supports or illustrates the section content), "
                "and 'bias_level' (one of: 'neutral', 'left', 'right' — your assessment of that specific quote's framing). "
                "Be selective: only cite sources that add a meaningfully distinct fact, figure, or perspective for that section. "
                "For a short or simple section where sources largely agree, 1-2 citations is appropriate. "
                "For a section covering competing viewpoints or multiple data points, cite enough to represent the range of perspectives. "
                "Do not pad citations by quoting the same point multiple times."
            ),
            "source_index": "List each source used with its article_id.",
        },
    }


def call_gemini(api_key, prompt):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[{"role": "user", "parts": [{"text": json.dumps(prompt)}]}],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OUTPUT_SCHEMA,
            temperature=0.3,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return json.loads(response.text)


# Path to the shared JSON store — relative to this script: ../../data/stories.json
STORIES_JSON_PATH = os.path.join(SCRIPT_DIR, "..", "data", "stories.json")


def save_story_to_json(story_wrapper_dict: dict, json_path: str = STORIES_JSON_PATH) -> None:
    """
    Append a StoryWrapper-compatible dict to the JSON store.
    Creates the file if it does not exist.
    """
    stories: list = []
    if os.path.exists(json_path) and os.path.getsize(json_path) > 2:
        with open(json_path, "r", encoding="utf-8") as f:
            stories = json.load(f)
    stories.append(story_wrapper_dict)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)
    print(f"Saved story '{story_wrapper_dict['story']['heading']}' → {json_path}")


def load_stories_from_json(json_path: str = STORIES_JSON_PATH) -> list:
    """Return list of StoryWrapper-compatible dicts from the JSON store."""
    if not os.path.exists(json_path) or os.path.getsize(json_path) <= 2:
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Maps Gemini's string bias labels to the float scale used by NewsProvider.bias_score
# (-1 = hard left, 0 = neutral, 1 = hard right)
BIAS_LEVEL_TO_FLOAT = {
    "left": -0.5,
    "neutral": 0.0,
    "right": 0.5,
}

DEFAULT_TRUST_SCORE = 0.7


def gemini_to_storywrapper(
    gemini_result: dict,
    credibility_scores: dict | None = None,
    provider_trust_map: dict | None = None,
) -> dict:
    """
    Convert the structured JSON returned by call_gemini() into a StoryWrapper-compatible dict.

    Args:
        gemini_result:      Output from call_gemini() — {title, standfirst, body_sections, source_index}.
        credibility_scores: Optional {article_id: float 0-1} from credibility_scoring.
                            Used as avg_truth per segment and as trust_score per provider.
        provider_trust_map: Optional {source_name: float 0-1} to pin a known outlet's trust score.
                            Takes priority over credibility_scores for trust_score.

    Returns:
        A plain dict matching the StoryWrapper schema:
        {
            "story": {
                "heading", "political_bias", "factual_accuracy",
                "sources": [...NewsProvider dicts...],
                "segments": [...Segment dicts...]
            },
            "comments": []
        }
        Instantiate with: StoryWrapper(**result)
    """
    credibility_scores = credibility_scores or {}
    provider_trust_map = provider_trust_map or {}

    # Registry of NewsProvider dicts, keyed by source name, built as we walk citations.
    # Bias score for a provider is the first bias_level we see for them.
    # Trust score priority: provider_trust_map > credibility_scores > DEFAULT_TRUST_SCORE.
    provider_registry: dict[str, dict] = {}

    def _get_or_create_provider(source_name: str, article_id: str, bias_level: str) -> dict:
        if source_name not in provider_registry:
            trust = provider_trust_map.get(
                source_name,
                credibility_scores.get(article_id, DEFAULT_TRUST_SCORE),
            )
            provider_registry[source_name] = {
                "name": source_name,
                "bias_score": BIAS_LEVEL_TO_FLOAT.get(bias_level, 0.0),
                "trust_score": round(float(trust), 3),
            }
        return provider_registry[source_name]

    segments = []

    for section in gemini_result.get("body_sections", []):
        citations = section.get("citations", [])

        seg_providers: dict[str, dict] = {}  # unique providers cited in this section
        bias_values: list[float] = []
        truth_values: list[float] = []

        for citation in citations:
            source = citation["source"]
            article_id = citation["article_id"]
            bias_level = citation.get("bias_level", "neutral")

            provider = _get_or_create_provider(source, article_id, bias_level)
            seg_providers[source] = provider
            bias_values.append(BIAS_LEVEL_TO_FLOAT.get(bias_level, 0.0))
            truth_values.append(credibility_scores.get(article_id, DEFAULT_TRUST_SCORE))

        avg_bias = round(sum(bias_values) / len(bias_values), 3) if bias_values else 0.0
        avg_truth = round(sum(truth_values) / len(truth_values), 3) if truth_values else DEFAULT_TRUST_SCORE

        segments.append({
            "text": f"{section['heading']}: {section['content']}",
            "sources": list(seg_providers.values()),
            "avg_bias": avg_bias,
            "avg_truth": avg_truth,
            "article_count": len(seg_providers),
            "notes": None,
            "comments": [],
        })

    # Ensure every source listed in source_index is in the registry
    # (some may not have appeared in any citation if Gemini omitted them from body_sections)
    for entry in gemini_result.get("source_index", []):
        source = entry["source"]
        article_id = entry["article_id"]
        if source not in provider_registry:
            trust = provider_trust_map.get(
                source,
                credibility_scores.get(article_id, DEFAULT_TRUST_SCORE),
            )
            provider_registry[source] = {
                "name": source,
                "bias_score": 0.0,
                "trust_score": round(float(trust), 3),
            }

    # Story-level scores: mean of all segment values
    all_bias = [s["avg_bias"] for s in segments]
    all_truth = [s["avg_truth"] for s in segments]
    political_bias = round(sum(all_bias) / len(all_bias), 3) if all_bias else 0.0
    factual_accuracy = round(sum(all_truth) / len(all_truth), 3) if all_truth else DEFAULT_TRUST_SCORE

    return {
        "story": {
            "heading": gemini_result["title"],
            "political_bias": political_bias,
            "factual_accuracy": factual_accuracy,
            "sources": list(provider_registry.values()),
            "segments": segments,
        },
        "comments": [],
    }


def main():
    api_key = load_api_key()
    articles = load_articles(DEFAULT_ARTICLES_DIR)

    print(f"Loaded {len(articles)} articles from: {DEFAULT_ARTICLES_DIR}")
    print(f"Calling {MODEL_NAME}...")

    prompt = build_prompt(articles)
    result = call_gemini(api_key, prompt)

    print("\n=== Raw Gemini Output ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # --- Conversion demo ---
    # Optionally supply credibility scores keyed by article_id (filename).
    # These would normally come from credibility_scoring.main(); hardcoded here for demo.
    demo_credibility = {article["article_id"]: 0.75 for article in articles}

    story_wrapper = gemini_to_storywrapper(result, credibility_scores=demo_credibility)

    print("\n=== StoryWrapper Dict ===")
    print(json.dumps(story_wrapper, indent=2, ensure_ascii=False))

    save_story_to_json(story_wrapper)


if __name__ == "__main__":
    main()
