import json
import os
import re
from datetime import datetime

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
        "category": {"type": "string"},
    },
    "required": ["title", "standfirst", "body_sections", "source_index", "category"],
}


def _load_env():
    """Load .env from project root, overriding any cached values."""
    env_path = os.path.join(SCRIPT_DIR, "..", "..", ".env")
    load_dotenv(env_path, override=True)


def get_llm_provider() -> str:
    """Return the configured LLM provider: 'gemini' or 'azure'."""
    _load_env()
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    return provider


def load_api_key():
    _load_env()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found. Add it to your .env file.")
    return api_key


def load_azure_config() -> dict:
    """Return Azure OpenAI connection details from env vars."""
    _load_env()
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    model_id = os.getenv("AZURE_AI_MODEL_ID", "gpt-5-mini")
    if not endpoint or not key:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY must be set in .env "
            "when LLM_PROVIDER=azure."
        )
    return {
        "endpoint": endpoint,
        "key": key,
        "api_version": api_version,
        "model": model_id,
    }


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
            "category": (
                "Assign exactly ONE single-word topic category that best describes the article. "
                "Choose from: Technology, Environment, Economy, Geopolitics, Finance, Health, "
                "Politics, Science, Education, Entertainment, Sport, Crime, Society, Business, Defence. "
                "Use only one word from this list."
            ),
        },
    }


def call_gemini(api_key, prompt, timeout_seconds: int = 120):
    """Call Gemini API with a timeout to prevent hanging."""
    import concurrent.futures

    client = genai.Client(api_key=api_key)

    def _call():
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=[{"role": "user", "parts": [{"text": json.dumps(prompt)}]}],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=OUTPUT_SCHEMA,
                temperature=0.3,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )

    print(f"[gemini] Calling {MODEL_NAME} (timeout={timeout_seconds}s)…")
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call)
        try:
            response = future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise RuntimeError(
                f"Gemini API call timed out after {timeout_seconds}s — "
                f"the prompt may be too large or the API is slow. "
                f"Try reducing max_per_source or MAX_ARTICLE_CHARS."
            )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    print(f"[gemini] Response received: {len(response.text):,} chars")
    return json.loads(response.text)


def call_azure_openai(azure_config: dict, prompt: dict, timeout_seconds: int = 120) -> dict:
    """Call Azure OpenAI with the same prompt structure used for Gemini."""
    import concurrent.futures
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=azure_config["endpoint"],
        api_key=azure_config["key"],
        api_version=azure_config["api_version"],
    )
    model = azure_config["model"]

    system_msg = (
        "You are a news aggregation assistant. You receive multiple source articles "
        "and produce a single consolidated, neutral news article in structured JSON.\n"
        "You MUST respond with valid JSON matching this schema:\n"
        + json.dumps(OUTPUT_SCHEMA, indent=2)
    )
    user_msg = json.dumps(prompt)

    def _call():
        return client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
        )

    print(f"[azure-openai] Calling {model} at {azure_config['endpoint']} (timeout={timeout_seconds}s)\u2026")
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call)
        try:
            response = future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise RuntimeError(
                f"Azure OpenAI call timed out after {timeout_seconds}s \u2014 "
                f"the prompt may be too large or the API is slow."
            )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Azure OpenAI returned an empty response.")
    print(f"[azure-openai] Response received: {len(content):,} chars "
          f"(usage: {response.usage.prompt_tokens}+{response.usage.completion_tokens} tokens)")
    return json.loads(content)


def call_llm(prompt: dict, timeout_seconds: int = 120) -> dict:
    """Unified LLM call — dispatches to Gemini or Azure OpenAI based on LLM_PROVIDER env var."""
    provider = get_llm_provider()
    print(f"[LLM] Provider = {provider!r} (from LLM_PROVIDER env var)")
    if provider == "azure":
        cfg = load_azure_config()
        return call_azure_openai(cfg, prompt, timeout_seconds=timeout_seconds)
    else:
        api_key = load_api_key()
        return call_gemini(api_key, prompt, timeout_seconds=timeout_seconds)


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
    article_metadata: list[dict] | None = None,
    agreement_scores: dict | None = None,
    contradiction_reports: list | None = None,
    missing_context: dict | None = None,
) -> dict:
    """
    Convert the structured JSON returned by call_gemini() into a StoryWrapper-compatible dict.

    Args:
        gemini_result:       Output from call_gemini() — {title, standfirst, body_sections, source_index}.
        credibility_scores:  Optional {article_id: float 0-1} from credibility_scoring.
        provider_trust_map:  Optional {source_name: float 0-1} to pin a known outlet's trust score.
        article_metadata:    Optional list of article dicts with id, title, url, source, published_at, text.
        agreement_scores:    Optional {article_id: float 0-1} from agreement_scoring.
        contradiction_reports: Optional list of contradiction dicts from agreement_scoring.
        missing_context:     Optional {article_id: [claim_strings]} from agreement_scoring.

    Returns:
        A plain dict matching the StoryWrapper schema.
    """
    credibility_scores = credibility_scores or {}
    provider_trust_map = provider_trust_map or {}
    agreement_scores = agreement_scores or {}
    contradiction_reports = contradiction_reports or []
    missing_context = missing_context or {}

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
    n_sections = len(gemini_result.get("body_sections", []))
    print(f"[gemini]   Building StoryWrapper: {n_sections} body sections, "
          f"{len(gemini_result.get('source_index', []))} sources")

    for sec_idx, section in enumerate(gemini_result.get("body_sections", [])):
        citations = section.get("citations", [])

        seg_providers: dict[str, dict] = {}  # unique providers cited in this section
        seg_citations: list[dict] = []  # citation objects with quotes
        bias_values: list[float] = []
        truth_values: list[float] = []

        for citation in citations:
            source = citation["source"]
            article_id = citation["article_id"]
            bias_level = citation.get("bias_level", "neutral")
            quote = citation.get("quote", "")

            provider = _get_or_create_provider(source, article_id, bias_level)
            seg_providers[source] = provider
            bias_values.append(BIAS_LEVEL_TO_FLOAT.get(bias_level, 0.0))
            truth_values.append(credibility_scores.get(article_id, DEFAULT_TRUST_SCORE))

            seg_citations.append({
                "source": source,
                "article_id": article_id,
                "quote": quote,
                "bias_level": bias_level,
            })

        avg_bias = round(sum(bias_values) / len(bias_values), 3) if bias_values else 0.0
        avg_truth = round(sum(truth_values) / len(truth_values), 3) if truth_values else DEFAULT_TRUST_SCORE

        # Compute per-segment agreement from the cited articles
        seg_agree_values = [agreement_scores.get(c["article_id"], 0.5) for c in seg_citations]
        avg_agreement = round(sum(seg_agree_values) / len(seg_agree_values), 3) if seg_agree_values else 0.5

        segments.append({
            "heading": section['heading'],
            "text": section['content'],
            "sources": list(seg_providers.values()),
            "citations": seg_citations,
            "avg_bias": avg_bias,
            "avg_truth": avg_truth,
            "avg_agreement": avg_agreement,
            "article_count": len(seg_providers),
            "notes": None,
            "comments": [],
        })
        cited_sources = [c['source'] for c in seg_citations]
        print(f"[gemini]     Section {sec_idx+1}/{n_sections}: \"{section['heading'][:50]}\" "
              f"— {len(seg_citations)} citations from {cited_sources}, "
              f"bias={avg_bias:.2f}, truth={avg_truth:.3f}, agree={avg_agreement:.3f}")

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
    all_agreement = [s["avg_agreement"] for s in segments]
    political_bias = round(sum(all_bias) / len(all_bias), 3) if all_bias else 0.0
    factual_accuracy = round(sum(all_truth) / len(all_truth), 3) if all_truth else DEFAULT_TRUST_SCORE
    source_agreement = round(sum(all_agreement) / len(all_agreement), 3) if all_agreement else 0.5

    # Build article metadata list
    articles_list = []
    if article_metadata:
        for meta in article_metadata:
            text = meta.get("text", "")
            articles_list.append({
                "id": meta.get("id", meta.get("article_id", "")),
                "title": meta.get("title", ""),
                "url": meta.get("url", "#"),
                "source": meta.get("source", "Unknown"),
                "published_at": meta.get("published_at"),
                "excerpt": (text[:200] + "\u2026") if len(text) > 200 else text,
            })

    def _slugify(text: str) -> str:
        t = text.lower()
        t = re.sub(r'[^a-z0-9]+', '-', t)
        return t.strip('-')

    # Category from Gemini (single-word topic)
    category = gemini_result.get("category", "General").strip().title()

    # updated_at = latest published_at from source articles (fall back to now)
    updated_at = datetime.utcnow().isoformat() + "Z"
    if article_metadata:
        dates = [m.get("published_at", "") for m in article_metadata if m.get("published_at")]
        if dates:
            latest = max(dates)  # YYYY-MM-DD strings sort lexicographically
            updated_at = latest + "T12:00:00Z"

    # Resolve source names for contradiction reports
    id_to_source: dict[str, str] = {}
    if article_metadata:
        for meta in article_metadata:
            id_to_source[meta.get("id", meta.get("article_id", ""))] = meta.get("source", "Unknown")

    resolved_contradictions = []
    for report in contradiction_reports:
        resolved_contradictions.append({
            "wrong_article": report["wrong_article"],
            "wrong_claim": report["wrong_claim"],
            "wrong_source": id_to_source.get(report["wrong_article"], "Unknown"),
            "correct_article": report["correct_article"],
            "correct_claim": report["correct_claim"],
            "correct_source": id_to_source.get(report["correct_article"], "Unknown"),
        })

    print(f"[gemini]   StoryWrapper complete: \"{gemini_result['title'][:60]}\"")
    print(f"[gemini]     category={category}, bias={political_bias:.2f}, "
          f"accuracy={factual_accuracy:.3f}, agreement={source_agreement:.3f}")
    print(f"[gemini]     {len(provider_registry)} providers, {len(segments)} segments, "
          f"{len(articles_list)} articles, {len(resolved_contradictions)} contradictions")

    return {
        "story": {
            "heading": gemini_result["title"],
            "slug": _slugify(gemini_result["title"]),
            "summary": gemini_result.get("standfirst", ""),
            "political_bias": political_bias,
            "factual_accuracy": factual_accuracy,
            "source_agreement": source_agreement,
            "sources": list(provider_registry.values()),
            "segments": segments,
            "articles": articles_list,
            "category": category,
            "updated_at": updated_at,
            "contradiction_reports": resolved_contradictions,
            "missing_context": dict(missing_context),
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
