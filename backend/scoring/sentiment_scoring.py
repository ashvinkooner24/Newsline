import time
import nltk
from transformers import pipeline as hf_pipeline

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize

# Lazy-loaded — not initialised until first call so FastAPI startup is instant
_subj_classifier = None
_sent_classifier = None


def _get_subj_classifier():
    """GroNLP subjectivity classifier (objective vs subjective)."""
    global _subj_classifier
    if _subj_classifier is None:
        print("[sentiment_scoring] Loading subjectivity classifier…")
        _subj_classifier = hf_pipeline(
            "text-classification",
            model="GroNLP/mdebertav3-subjectivity-english",
            top_k=None,
        )
    return _subj_classifier


def _get_sent_classifier():
    """Cardiff NLP sentiment classifier (negative / neutral / positive)."""
    global _sent_classifier
    if _sent_classifier is None:
        print("[sentiment_scoring] Loading sentiment classifier (twitter-roberta)…")
        _sent_classifier = hf_pipeline(
            "text-classification",
            model="cardiffnlp/twitter-roberta-base-sentiment",
            top_k=None,
        )
    return _sent_classifier


# Labels that represent "neutral" in the twitter-roberta sentiment model
_NEUTRAL_LABELS = {"neutral", "LABEL_1"}


def _extract_neutrality(sent_result: list[dict]) -> float:
    """Extract the neutral probability from twitter-roberta output."""
    for item in sent_result:
        if item["label"] in _NEUTRAL_LABELS:
            return item["score"]
    return 0.33  # fallback


def score_sentence(sentence: str):
    """
    Return (objectivity, subjectivity) for a single sentence.

    Combines GroNLP subjectivity with twitter-roberta sentiment neutrality
    so that factual reporting about negative events is not penalised.
    """
    subj_result = _get_subj_classifier()(sentence)[0]
    subj_score = next(
        (item["score"] for item in subj_result if item["label"] == "LABEL_1"), 0.5
    )

    sent_result = _get_sent_classifier()(sentence)[0]
    neutrality = _extract_neutrality(sent_result)

    raw_objectivity = 1 - subj_score
    # Blend: 60% subjectivity model, 40% sentiment neutrality
    # High neutrality boosts objectivity for factual articles about emotional topics
    objectivity = 0.6 * raw_objectivity + 0.4 * neutrality
    return objectivity, 1 - objectivity


def score_article(text: str):
    """
    Return (objectivity, subjectivity) for a whole article,
    weighted by sentence length.  Values are in [0, 1].

    Uses both the GroNLP subjectivity classifier and the Cardiff NLP
    twitter-roberta-base-sentiment model.  The sentiment neutrality score
    corrects for factual articles about emotionally charged topics that the
    subjectivity model alone would penalise.
    """
    sentences = sent_tokenize(text)
    if not sentences:
        return 0.5, 0.5

    subj_clf = _get_subj_classifier()
    sent_clf = _get_sent_classifier()

    total_weighted_subj = 0.0
    total_weighted_neutrality = 0.0
    total_weight = 0
    t0 = time.time()
    n = len(sentences)

    for i, sentence in enumerate(sentences):
        weight = len(sentence.split())
        if weight == 0:
            continue

        subj_result = subj_clf(sentence)[0]
        subj_score = next(
            (item["score"] for item in subj_result if item["label"] == "LABEL_1"), 0.5
        )

        sent_result = sent_clf(sentence)[0]
        neutrality = _extract_neutrality(sent_result)

        total_weighted_subj += subj_score * weight
        total_weighted_neutrality += neutrality * weight
        total_weight += weight

        # Log progress every 20 sentences
        if (i + 1) % 20 == 0:
            print(f"[sentiment]     sentence {i+1}/{n} ({time.time()-t0:.1f}s elapsed)")

    if n > 10:
        print(f"[sentiment]   Scored {n} sentences in {time.time()-t0:.1f}s")

    if total_weight == 0:
        return 0.5, 0.5

    avg_subjectivity = total_weighted_subj / total_weight
    avg_neutrality = total_weighted_neutrality / total_weight

    raw_objectivity = 1 - avg_subjectivity
    # Blend: 60% subjectivity model, 40% sentiment neutrality
    objectivity = 0.6 * raw_objectivity + 0.4 * avg_neutrality
    subjectivity = 1 - objectivity

    return objectivity, subjectivity

def main():

    with open("../scraping/rag-source/article/The_guardian/Iran_refusing_to_export_highly_enriched_uranium_but_willing_to_dilute_purity,_sources_say.txt", "r", encoding="utf-8") as file:
        text = file.read()
    
    scores = score_article(text)
    print(scores)

    with open("../scraping/rag-source/article/The_guardian/The_Liberal_party_believes_Trump-style_politics_is_the_way_to_win_back_power._But_it_just_won’t_work_in_urban_Australia_|_Zoe_Daniel.txt", "r", encoding="utf-8") as file:
        text = file.read()
    
    scores = score_article(text)
    print(scores)

    with open("../scraping/rag-source/article/tests/trump_post.txt", "r", encoding="utf-8") as file:
        text = file.read()
    
    scores = score_article(text)
    print(scores)

if __name__ == "__main__":
    main()