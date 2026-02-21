"""
RAG Summary Generator (stub)

Production implementation would:
  1. Retrieve the top-K most relevant chunks for a topic from the vector DB
     using the topic centroid as the query vector.
  2. Inject those chunks into an LLM prompt (GPT-4o, Claude Sonnet, Gemini Pro)
     structured to produce a neutral, citation-backed prose summary.
  3. Parse the model output to extract inline citation tokens [1], [2], …
  4. Build a CitationMapping list linking each token back to its source chunk.

Dependencies (when implementing):
    pip install openai anthropic
"""

from __future__ import annotations

from models.topic import CitationMapping


SUMMARY_PROMPT_TEMPLATE = """
You are a neutral news aggregation assistant. 
Summarise the following article excerpts into a single, balanced, factual paragraph.
Cite each claim with inline tokens [1], [2], etc. matching the provided sources.
Do not express any political opinion. Flag any contradictions between sources.

Sources:
{sources_block}

Write a concise 150-200 word summary:
"""


def build_rag_summary(
    topic_name: str,
    chunks: list[dict],  # [{"id": ..., "source": ..., "text": ...}]
) -> tuple[str, list[CitationMapping]]:
    """
    STUB: Generate a RAG summary with citation mapping for a topic.

    Returns:
        summary_text: Prose summary with inline citation tokens.
        citations: List of CitationMapping objects.
    """
    # Build a simple extractive stub: concatenate first sentence of each chunk
    sentences = []
    citations: list[CitationMapping] = []

    for i, chunk in enumerate(chunks[:6], start=1):
        token = f"[{i}]"
        first_sentence = chunk["text"].split(".")[0].strip() + "."
        sentences.append(f"{first_sentence} {token}")
        citations.append(
            CitationMapping(
                citation_id=token,
                article_id=chunk.get("article_id", "unknown"),
                segment_id=chunk.get("segment_id", "unknown"),
                source_name=chunk.get("source", "Unknown Source"),
                excerpt=first_sentence,
                url=chunk.get("url"),
            )
        )

    summary = f"[STUB SUMMARY — {topic_name}] " + " ".join(sentences)
    return summary, citations
