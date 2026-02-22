import os
import nltk
import torch
import itertools
from collections import defaultdict
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np
import re

nltk.download('punkt', quiet=True)

# ==============================
# CONFIG
# ==============================
SIMILARITY_THRESHOLD = 0.75
CLAIM_OBJECTIVITY_THRESHOLD = 0.6
MISSING_CONTEXT_SIM_THRESHOLD = 0.8
DEFAULT_REPUTATION = 0.5

# ==============================
# LAZY MODEL LOADERS
# ==============================
_embedder = None
_nli_tokenizer = None
_nli_model = None
_nli_device = None
_classifier = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        print("[agreement_scoring] Loading embedding model…")
        _embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _embedder

def _get_nli():
    global _nli_tokenizer, _nli_model, _nli_device
    if _nli_model is None:
        print("[agreement_scoring] Loading NLI model…")
        name = "facebook/bart-large-mnli"
        _nli_tokenizer = AutoTokenizer.from_pretrained(name)
        _nli_model = AutoModelForSequenceClassification.from_pretrained(name)
        _nli_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _nli_model.to(_nli_device)
    return _nli_tokenizer, _nli_model, _nli_device

def _get_classifier():
    global _classifier
    if _classifier is None:
        print("[agreement_scoring] Loading subjectivity classifier…")
        _classifier = pipeline(
            "text-classification",
            model="GroNLP/mdebertav3-subjectivity-english",
            top_k=None,
        )
    return _classifier

# ==============================
# UTIL FUNCTIONS
# ==============================

def score_sentence(sentence):
    result = _get_classifier()(sentence)[0]
    subj_score = next((item["score"] for item in result if item["label"] == "LABEL_1"), 0.5)
    obj_score = 1 - subj_score
    return obj_score, subj_score

def score_article(text):
    sentences = nltk.sent_tokenize(text)
    weighted_sum = 0
    total_words = 0
    for s in sentences:
        obj, subj = score_sentence(s)
        weight = len(s.split())
        weighted_sum += obj * weight
        total_words += weight
    article_obj = weighted_sum / total_words if total_words > 0 else 0
    return article_obj, 1 - article_obj

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

def extract_claims(article):
    sentences = nltk.sent_tokenize(article["text"])
    claims = []
    for s in sentences:
        obj, subj = score_sentence(s)
        if obj >= CLAIM_OBJECTIVITY_THRESHOLD and len(s.split()) > 6 and not s.strip().endswith("?"):
            claims.append({"text": s.strip(), "objectivity": obj})
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

def compute_agreement(articles):
    """
    Given a list of article dicts (each with 'id', 'text', 'objectivity'),
    return:
      (agreement_scores, contradiction_reports, missing_context)

      agreement_scores     : dict[article_id -> float 0-1]
      contradiction_reports: list[dict]
      missing_context      : dict[article_id -> list[str]]
    """
    embedder = _get_embedder()

    # Extract high-objectivity claims
    for article in articles:
        article["claims"] = extract_claims(article)

    all_claims = []
    claim_meta = []

    for article in articles:
        for claim in article["claims"]:
            all_claims.append(claim["text"])
            claim_meta.append({
                "article_id": article["id"],
                "article_obj": article["objectivity"],
                "claim_obj": claim["objectivity"],
            })

    if not all_claims:
        empty = {a["id"]: 0.5 for a in articles}
        return empty, [], defaultdict(list)

    # Embed claims
    claim_embeddings = embedder.encode(all_claims, convert_to_tensor=True)

    # Relations and truth voting
    relations = []
    contradictions_list = []
    truth_votes = defaultdict(float)
    article_support = defaultdict(float)
    article_contradiction = defaultdict(float)

    for i, j in itertools.combinations(range(len(all_claims)), 2):
        sim = util.cos_sim(claim_embeddings[i], claim_embeddings[j]).item()
        if sim > SIMILARITY_THRESHOLD:
            # Skip if numbers or years differ
            if has_different_numbers_or_years(all_claims[i], all_claims[j]):
                continue
            result = classify_nli(all_claims[i], all_claims[j])
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

    # ==============================
    # Article Scores  →  agreement_scores dict[id -> float]
    # ==============================
    agreement_scores = {}
    for article in articles:
        aid = article["id"]
        total_weight = sum(c["objectivity"] for c in article["claims"]) or 1
        supported = article_support.get(aid, 0)
        contradicted = article_contradiction.get(aid, 0)
        consistency = (supported - contradicted) / total_weight + 0.5 * article["objectivity"]
        agreement_scores[aid] = round(max(0.0, min(1.0, consistency)), 3)

    # ==============================
    # Missing Context
    # ==============================
    threshold = np.percentile(list(truth_votes.values()), 75) if truth_votes else 0
    core_claims_idx = [idx for idx, vote in truth_votes.items() if vote > threshold]

    missing_context = defaultdict(list)
    for idx in core_claims_idx:
        claim_text = all_claims[idx]
        claim_embed = claim_embeddings[idx]
        for article in articles:
            found_similar = False
            for sent in nltk.sent_tokenize(article["text"]):
                sent_embed = embedder.encode(sent, convert_to_tensor=True)
                sim = util.cos_sim(claim_embed, sent_embed).item()
                if sim > MISSING_CONTEXT_SIM_THRESHOLD:
                    found_similar = True
                    break
            if not found_similar:
                missing_context[article["id"]].append(claim_text)
    missing_context = dict(missing_context)

    # ==============================
    # Contradiction Reports
    # ==============================
    contradiction_reports = []
    for i, j in contradictions_list:
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