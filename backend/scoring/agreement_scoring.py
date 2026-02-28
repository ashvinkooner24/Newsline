import os
import nltk
import torch
import itertools
import time
from collections import defaultdict
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import re

nltk.download('punkt', quiet=True)

# Import scoring from sentiment_scoring (shared with pipeline)
try:
    from .sentiment_scoring import score_sentence, score_article
except ImportError:
    from sentiment_scoring import score_sentence, score_article  # type: ignore

# ==============================
# CONFIG
# ==============================
SIMILARITY_THRESHOLD = 0.82          # Higher bar — only very similar claims get NLI compared
CLAIM_OBJECTIVITY_THRESHOLD = 0.6
MISSING_CONTEXT_SIM_THRESHOLD = 0.85  # Higher bar — must be very clearly the same claim
MIN_CLAIM_WORDS = 8                   # Skip very short or list-like sentences
MIN_SOURCES_FOR_CONTRADICTIONS = 3    # Don't flag contradictions with <3 sources
MIN_SOURCES_FOR_MISSING_CTX = 3       # Don't flag missing context with <3 sources
DEFAULT_REPUTATION = 0.65

# ==============================
# LAZY MODEL LOADERS
# ==============================
_embedder = None
_nli_tokenizer = None
_nli_model = None
_nli_device = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        print("[agreement_scoring] Loading embedding model (all-MiniLM-L6-v2)…")
        t0 = time.time()
        _embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print(f"[agreement_scoring] Embedding model loaded in {time.time()-t0:.1f}s")
    return _embedder

def _get_nli():
    global _nli_tokenizer, _nli_model, _nli_device
    if _nli_model is None:
        print("[agreement_scoring] Loading NLI model (facebook/bart-large-mnli)…")
        t0 = time.time()
        name = "facebook/bart-large-mnli"
        _nli_tokenizer = AutoTokenizer.from_pretrained(name)
        _nli_model = AutoModelForSequenceClassification.from_pretrained(name)
        _nli_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _nli_model.to(_nli_device)
        print(f"[agreement_scoring] NLI model loaded in {time.time()-t0:.1f}s (device={_nli_device})")
    return _nli_tokenizer, _nli_model, _nli_device

# ==============================
# UTIL FUNCTIONS
# ==============================

def load_articles(articles_dir):
    """Load .txt files from articles_dir and score their objectivity."""
    articles = []
    for filename in os.listdir(articles_dir):
        if filename.endswith(".txt"):
            path = os.path.join(articles_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            obj, subj = score_article(text)
            articles.append({
                "id": filename,
                "text": text,
                "source": "unknown",
                "reputation": DEFAULT_REPUTATION,
                "objectivity": obj,
                "subjectivity": subj,
            })
    return articles

# Regex to detect list/enumeration sentences (e.g. medal tallies, rankings)
_LIST_PATTERN = re.compile(
    r'(\d+\s*(gold|silver|bronze|total|medal|point|score|rank)'
    r'|^\s*\d+\.\s'
    r'|\n\s*\d+\.)',
    re.IGNORECASE,
)


def _is_list_or_enumeration(sentence: str) -> bool:
    """Return True if the sentence looks like a list item, table row, or tally."""
    # Has multiple numbers separated by commas/parentheses — likely a stat line
    numbers = re.findall(r'\d+', sentence)
    if len(numbers) >= 4:
        return True
    if _LIST_PATTERN.search(sentence):
        return True
    # Very short with mostly numbers
    words = sentence.split()
    if len(words) > 0 and sum(1 for w in words if re.match(r'\d', w)) / len(words) > 0.4:
        return True
    return False


def extract_claims(article):
    sentences = nltk.sent_tokenize(article["text"])
    claims = []
    for s in sentences:
        stripped = s.strip()
        # Skip questions, very short sentences, and list/enumeration lines
        if stripped.endswith("?"):
            continue
        if len(stripped.split()) < MIN_CLAIM_WORDS:
            continue
        if _is_list_or_enumeration(stripped):
            continue
        obj, subj = score_sentence(stripped)
        if obj >= CLAIM_OBJECTIVITY_THRESHOLD:
            claims.append({"text": stripped, "objectivity": obj})
    return claims

def classify_nli(claim1, claim2):
    nli_tokenizer, nli_model, device = _get_nli()
    inputs = nli_tokenizer(claim1, claim2, return_tensors="pt", truncation=True).to(device)
    outputs = nli_model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    labels = ["contradiction", "neutral", "entailment"]
    return labels[torch.argmax(probs)]

def has_different_numbers_or_years(claim1, claim2):
    numbers1 = re.findall(r'\d+', claim1)
    numbers2 = re.findall(r'\d+', claim2)
    if not numbers1 or not numbers2:
        return False
    return not any(n in numbers2 for n in numbers1)

# ==============================
# PUBLIC API
# ==============================

def compute_agreement(articles, skip_contradictions: bool = False):
    """
    Given a list of article dicts (each with 'id', 'text', 'objectivity'),
    return:
      (agreement_scores, contradiction_reports, missing_context)

      agreement_scores     : dict[article_id -> float 0-1]
      contradiction_reports: list[dict]
      missing_context      : dict[article_id -> list[str]]

    If skip_contradictions is True (e.g. for sports topics or <3 sources),
    skip all NLI work and return neutral agreement scores immediately.
    """
    # ── Fast path: skip all heavy ML work ──
    if skip_contradictions:
        print("[agreement]   skip_contradictions=True — returning neutral scores (no claim extraction / NLI)")
        scores = {
            a["id"]: round(0.55 + 0.15 * a.get("objectivity", 0.5), 3)
            for a in articles
        }
        return scores, [], {}

    embedder = _get_embedder()

    # Extract high-objectivity claims (capped to prevent O(n²) explosion)
    MAX_CLAIMS_PER_ARTICLE = 15
    t0 = time.time()
    for idx, article in enumerate(articles):
        n_sentences = len(nltk.sent_tokenize(article["text"]))
        article["claims"] = extract_claims(article)
        original_count = len(article["claims"])
        if original_count > MAX_CLAIMS_PER_ARTICLE:
            article["claims"] = article["claims"][:MAX_CLAIMS_PER_ARTICLE]
        src = article.get('source', article['id'])
        title = article.get('title', article['id'])[:50]
        capped = f" (capped from {original_count})" if original_count > MAX_CLAIMS_PER_ARTICLE else ""
        print(f"[agreement]     Article {idx+1}/{len(articles)} [{src}]: "
              f"{len(article['claims'])} claims from {n_sentences} sentences{capped} "
              f"| {title}…")

    # Build source lookup for fast same-source checks
    _id_to_source = {a["id"]: a.get("source", "unknown") for a in articles}

    all_claims = []
    claim_meta = []

    for article in articles:
        for claim in article["claims"]:
            all_claims.append(claim["text"])
            claim_meta.append({
                "article_id": article["id"],
                "article_source": _id_to_source[article["id"]],
                "article_obj": article["objectivity"],
                "claim_obj": claim["objectivity"],
            })

    print(f"[agreement]   Extracted {len(all_claims)} claims from {len(articles)} articles in {time.time()-t0:.1f}s")

    if not all_claims:
        print(f"[agreement]   No claims found — returning neutral scores")
        empty = {a["id"]: 0.5 for a in articles}
        return empty, [], defaultdict(list)

    # Embed claims
    t0 = time.time()
    claim_embeddings = embedder.encode(all_claims, convert_to_tensor=True)
    print(f"[agreement]   Embedded {len(all_claims)} claims in {time.time()-t0:.1f}s")

    # Relations and truth voting
    total_pairs = len(all_claims) * (len(all_claims) - 1) // 2
    print(f"[agreement]   Comparing {total_pairs:,} claim pairs (NLI on similar ones)…")
    t0 = time.time()
    relations = []
    contradictions_list = []
    truth_votes = defaultdict(float)
    article_support = defaultdict(float)
    article_contradiction = defaultdict(float)
    nli_calls = 0

    for i, j in itertools.combinations(range(len(all_claims)), 2):
        # Skip claims from the same source — a source can't contradict itself
        if claim_meta[i]["article_source"] == claim_meta[j]["article_source"]:
            continue
        sim = util.cos_sim(claim_embeddings[i], claim_embeddings[j]).item()
        if sim > SIMILARITY_THRESHOLD:
            # Skip if numbers or years differ
            if has_different_numbers_or_years(all_claims[i], all_claims[j]):
                continue
            result = classify_nli(all_claims[i], all_claims[j])
            nli_calls += 1
            if nli_calls % 50 == 0:
                print(f"[agreement]     NLI call #{nli_calls} ({time.time()-t0:.1f}s elapsed)")
            if result in ["entailment", "contradiction"]:
                relations.append((i, j, result))

                # Compute weight using article + claim objectivity
                weight_i = claim_meta[i]["article_obj"] * claim_meta[i]["claim_obj"]
                weight_j = claim_meta[j]["article_obj"] * claim_meta[j]["claim_obj"]

                if result == "entailment":
                    truth_votes[i] += weight_j
                    truth_votes[j] += weight_i
                    article_support[claim_meta[i]["article_id"]] += weight_j
                    article_support[claim_meta[j]["article_id"]] += weight_i

                if result == "contradiction":
                    truth_votes[i] -= weight_j
                    truth_votes[j] -= weight_i
                    article_contradiction[claim_meta[i]["article_id"]] += weight_j
                    article_contradiction[claim_meta[j]["article_id"]] += weight_i
                    contradictions_list.append((i, j))

    print(f"[agreement]   NLI complete: {nli_calls} calls, "
          f"{len([r for r in relations if r[2]=='entailment'])} entailments, "
          f"{len(contradictions_list)} contradictions in {time.time()-t0:.1f}s")

    # ==============================
    # Article Scores  →  agreement_scores dict[id -> float]
    # ==============================
    agreement_scores = {}
    for article in articles:
        aid = article["id"]
        supported = article_support.get(aid, 0)
        contradicted = article_contradiction.get(aid, 0)
        matched = supported + contradicted
        if matched > 0:
            # Ratio of support vs contradiction → scaled to [0.05, 0.95]
            net_ratio = (supported - contradicted) / matched
            consistency = 0.5 + 0.45 * net_ratio
        else:
            # No claim matches found → neutral baseline boosted by objectivity
            consistency = 0.55 + 0.15 * article["objectivity"]
        agreement_scores[aid] = round(max(0.05, min(1.0, consistency)), 3)

    # Print per-article agreement summary
    print(f"[agreement]   Per-article agreement scores:")
    for article in articles:
        aid = article["id"]
        src = article.get('source', aid)
        sup = article_support.get(aid, 0)
        con = article_contradiction.get(aid, 0)
        print(f"[agreement]     [{src}] agree={agreement_scores[aid]:.3f} "
              f"(support={sup:.2f}, contradiction={con:.2f})")

    # ==============================
    # Source count gate — skip contradiction/missing-ctx for low-source topics
    # ==============================
    unique_sources = set(a.get('source', '') for a in articles)
    num_sources = len(unique_sources)
    print(f"[agreement]   {num_sources} unique sources: {sorted(unique_sources)}")

    if num_sources < MIN_SOURCES_FOR_CONTRADICTIONS:
        print(f"[agreement]   Skipping contradictions — only {num_sources} sources (need {MIN_SOURCES_FOR_CONTRADICTIONS})")
        contradictions_list = []  # clear all contradictions

    # ==============================
    # Missing Context
    # ==============================
    t0 = time.time()
    if num_sources < MIN_SOURCES_FOR_MISSING_CTX:
        print(f"[agreement]   Skipping missing context — only {num_sources} sources (need {MIN_SOURCES_FOR_MISSING_CTX})")
        missing_context = dict()
        print(f"[agreement]   Missing context done in 0.0s — 0 missing claims across 0 articles")
        contradiction_reports = []
        print(f"[agreement]   Building 0 contradiction reports…")
        return agreement_scores, contradiction_reports, missing_context

    threshold = np.percentile(list(truth_votes.values()), 75) if truth_votes else 0
    core_claims_idx = [idx for idx, vote in truth_votes.items() if vote > threshold]
    # Cap to avoid O(n*m) explosion with many core claims
    MAX_CORE_CLAIMS = 10
    if len(core_claims_idx) > MAX_CORE_CLAIMS:
        print(f"[agreement]   Capping core claims from {len(core_claims_idx)} to {MAX_CORE_CLAIMS}")
        core_claims_idx = core_claims_idx[:MAX_CORE_CLAIMS]
    print(f"[agreement]   Checking {len(core_claims_idx)} core claims for missing context across {len(articles)} articles…")

    missing_context = defaultdict(list)
    for ci, idx in enumerate(core_claims_idx):
        claim_text = all_claims[idx]
        claim_embed = claim_embeddings[idx]
        claim_src = claim_meta[idx]["article_id"]
        print(f"[agreement]     Core claim {ci+1}/{len(core_claims_idx)}: "
              f"\"{claim_text[:60]}…\" (from {claim_src})")
        for article in articles:
            found_similar = False
            sents = nltk.sent_tokenize(article["text"])
            for sent in sents:
                sent_embed = embedder.encode(sent, convert_to_tensor=True)
                sim = util.cos_sim(claim_embed, sent_embed).item()
                if sim > MISSING_CONTEXT_SIM_THRESHOLD:
                    found_similar = True
                    break
            if not found_similar:
                src = article.get('source', article['id'])
                print(f"[agreement]       ✗ Missing in [{src}]")
                missing_context[article["id"]].append(claim_text)
    missing_context = dict(missing_context)
    print(f"[agreement]   Missing context done in {time.time()-t0:.1f}s — "
          f"{sum(len(v) for v in missing_context.values())} missing claims across {len(missing_context)} articles")

    # ==============================
    # Contradiction Reports
    # ==============================
    contradiction_reports = []
    print(f"[agreement]   Building {len(contradictions_list)} contradiction reports…")
    for ci, (i, j) in enumerate(contradictions_list):
        claim1 = all_claims[i]
        claim2 = all_claims[j]
        meta1 = claim_meta[i]
        meta2 = claim_meta[j]

        weight1 = meta1["article_obj"] * meta1["claim_obj"]
        weight2 = meta2["article_obj"] * meta2["claim_obj"]

        if weight1 <= weight2:
            wrong_article, wrong_claim = meta1["article_id"], claim1
            correct_article, correct_claim = meta2["article_id"], claim2
        else:
            wrong_article, wrong_claim = meta2["article_id"], claim2
            correct_article, correct_claim = meta1["article_id"], claim1

        contradiction_reports.append({
            "wrong_article": wrong_article,
            "wrong_claim": wrong_claim,
            "correct_article": correct_article,
            "correct_claim": correct_claim,
        })
        # Find source names for readable output
        wrong_src = next((a.get('source', wrong_article) for a in articles if a['id'] == wrong_article), wrong_article)
        correct_src = next((a.get('source', correct_article) for a in articles if a['id'] == correct_article), correct_article)
        print(f"[agreement]     Contradiction #{ci+1}: [{wrong_src}] vs [{correct_src}]")
        print(f"[agreement]       Wrong:   \"{wrong_claim[:70]}…\"")
        print(f"[agreement]       Correct: \"{correct_claim[:70]}…\"")

    return agreement_scores, contradiction_reports, missing_context


# ==============================
# STANDALONE TEST
# ==============================

def main():
    import sys
    articles_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "test")
    articles = load_articles(articles_dir)
    agreement_scores, contradiction_reports, missing_context = compute_agreement(articles)

    print("\n==== Agreement Scores ====")
    for aid, score in agreement_scores.items():
        print(aid, score)

    print("\n==== Missing Context ====")
    for aid, claims in missing_context.items():
        print(f"\n{aid} missing {len(claims)} core claims")
        for c in claims[:3]:
            print("-", c)

    print("\n==== Contradictions ====")
    for report in contradiction_reports:
        print(f"\nArticle flagged as WRONG: {report['wrong_article']}")
        print("Wrong claim:", report['wrong_claim'])
        print("Contradicted by article:", report['correct_article'])
        print("Correct claim:", report['correct_claim'])

if __name__ == "__main__":
    main()