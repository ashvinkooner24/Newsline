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


def main():
    api_key = load_api_key()
    articles = load_articles(DEFAULT_ARTICLES_DIR)

    print(f"Loaded {len(articles)} articles from: {DEFAULT_ARTICLES_DIR}")
    print(f"Calling {MODEL_NAME}...")

    prompt = build_prompt(articles)
    result = call_gemini(api_key, prompt)

    print("\n=== Aggregated Article ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
