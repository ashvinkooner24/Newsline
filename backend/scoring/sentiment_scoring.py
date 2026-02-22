import nltk
from transformers import pipeline

nltk.download('punkt')
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

# Load model
classifier = pipeline(
    "text-classification",
    model="GroNLP/mdebertav3-subjectivity-english",
    top_k=None
)

def score_article(text):
    sentences = sent_tokenize(text)
    
    total_weighted_score = 0
    total_weight = 0
    
    for sentence in sentences:
        result = classifier(sentence)[0]
        
        # Get subjectivity score
        subjectivity_score = None
        for item in result:
            if item["label"] == "LABEL_1":  # Assuming LABEL_1 = subjective
                subjectivity_score = item["score"]
        
        # Weight by sentence length
        weight = len(sentence.split())
        
        total_weighted_score += subjectivity_score * weight
        total_weight += weight
    
    article_subjectivity = total_weighted_score / total_weight
    article_objectivity = 1 - article_subjectivity
    
    return {
        "subjective_percent": round(article_subjectivity * 100, 2),
        "objective_percent": round(article_objectivity * 100, 2)
    }

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