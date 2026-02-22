import nltk
from transformers import pipeline as hf_pipeline

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize

# Lazy-loaded — not initialised until first call so FastAPI startup is instant
_classifier = None

def _get_classifier():
    global _classifier
    if _classifier is None:
        print("[sentiment_scoring] Loading subjectivity classifier…")
        _classifier = hf_pipeline(
            "text-classification",
            model="GroNLP/mdebertav3-subjectivity-english",
            top_k=None,
        )
    return _classifier


def score_sentence(sentence: str):
    """Return (objectivity, subjectivity) floats for a single sentence."""
    result = _get_classifier()(sentence)[0]
    subj = next((item["score"] for item in result if item["label"] == "LABEL_1"), 0.5)
    return 1 - subj, subj


def score_article(text: str):
    """
    Return (objectivity, subjectivity) floats for a whole article,
    weighted by sentence length.  Values are in [0, 1].
    """
    sentences = sent_tokenize(text)

    total_weighted_score = 0
    total_weight = 0

    for sentence in sentences:
        result = _get_classifier()(sentence)[0]

        subjectivity_score = next(
            (item["score"] for item in result if item["label"] == "LABEL_1"), 0.5
        )

        weight = len(sentence.split())
        total_weighted_score += subjectivity_score * weight
        total_weight += weight

    article_subjectivity = total_weighted_score / total_weight if total_weight else 0.5
    article_objectivity = 1 - article_subjectivity

    return article_objectivity, article_subjectivity

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