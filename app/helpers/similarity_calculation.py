from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_similarity_and_confidence(original_text, cleaned_text):
    """
    Returns:
    - similarity (as percentage, 0–100)
    - confidence score (as percentage, 0–100)
    """
    vectorizer = TfidfVectorizer().fit([original_text, cleaned_text])
    vectors = vectorizer.transform([original_text, cleaned_text])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

    retention_ratio = len(cleaned_text) / len(original_text) if len(original_text) > 0 else 0

    # Compute raw confidence out of 10
    raw_confidence = (similarity * 7 + retention_ratio * 3)
    raw_confidence = min(10.0, max(0.0, raw_confidence))

    # Convert both to percentages
    similarity_percent = round(similarity * 100, 2)
    confidence_percent = round(raw_confidence * 10, 2)  # since it's out of 10

    return similarity_percent, confidence_percent
