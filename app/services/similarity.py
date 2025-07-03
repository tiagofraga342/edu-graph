import numpy as np
from numpy import dot
from numpy.linalg import norm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
import re
from typing import List, Dict, Tuple, Optional
from collections import Counter
import math

def cosine_similarity(vec1, vec2):
    """Basic cosine similarity between two vectors"""
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def semantic_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Enhanced semantic similarity using embeddings"""
    return cosine_similarity(embedding1, embedding2)

def keyword_overlap_similarity(text1: str, text2: str) -> float:
    """Calculate similarity based on keyword overlap using TF-IDF"""
    if not text1.strip() or not text2.strip():
        return 0.0

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),  # Include bigrams
        max_features=1000,
        lowercase=True
    )

    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except:
        return 0.0

def structural_similarity(text1: str, text2: str) -> float:
    """Calculate similarity based on document structure (headers, lists, etc.)"""
    def extract_structure_features(text: str) -> Dict[str, int]:
        features = {
            'headers': len(re.findall(r'^#+\s', text, re.MULTILINE)),
            'lists': len(re.findall(r'^\s*[-*+]\s', text, re.MULTILINE)),
            'numbered_lists': len(re.findall(r'^\s*\d+\.\s', text, re.MULTILINE)),
            'code_blocks': len(re.findall(r'```', text)),
            'links': len(re.findall(r'\[.*?\]\(.*?\)', text)),
            'bold_text': len(re.findall(r'\*\*.*?\*\*', text)),
            'italic_text': len(re.findall(r'\*.*?\*', text)),
        }
        return features

    features1 = extract_structure_features(text1)
    features2 = extract_structure_features(text2)

    # Calculate cosine similarity of structure vectors
    vec1 = list(features1.values())
    vec2 = list(features2.values())

    if sum(vec1) == 0 and sum(vec2) == 0:
        return 1.0  # Both have no structure
    if sum(vec1) == 0 or sum(vec2) == 0:
        return 0.0  # One has structure, other doesn't

    return cosine_similarity(vec1, vec2)

def topic_similarity(text1: str, text2: str) -> float:
    """Calculate topic-based similarity using simple keyword extraction"""
    def extract_keywords(text: str) -> List[str]:
        # Simple keyword extraction (you could use more sophisticated methods)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter out common words (basic stop words)
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'she', 'use', 'her', 'now', 'oil', 'sit', 'set'}
        return [word for word in words if word not in stop_words and len(word) > 3]

    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))

    if not keywords1 and not keywords2:
        return 0.0
    if not keywords1 or not keywords2:
        return 0.0

    intersection = len(keywords1.intersection(keywords2))
    union = len(keywords1.union(keywords2))

    return intersection / union if union > 0 else 0.0

def calculate_comprehensive_similarity(
    text1: str, text2: str,
    embedding1: List[float], embedding2: List[float],
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculate multiple types of similarity and return a comprehensive score

    Args:
        text1, text2: The text content of the notes
        embedding1, embedding2: Pre-computed embeddings
        weights: Optional weights for different similarity types

    Returns:
        Dictionary with different similarity scores and overall score
    """
    if weights is None:
        weights = {
            'semantic': 0.4,      # Semantic meaning (embeddings)
            'keyword': 0.3,       # Keyword overlap (TF-IDF)
            'structural': 0.15,   # Document structure
            'topic': 0.15         # Topic similarity
        }

    similarities = {
        'semantic': semantic_similarity(embedding1, embedding2),
        'keyword': keyword_overlap_similarity(text1, text2),
        'structural': structural_similarity(text1, text2),
        'topic': topic_similarity(text1, text2)
    }

    # Calculate weighted overall score
    overall_score = sum(similarities[key] * weights[key] for key in similarities.keys())
    similarities['overall'] = overall_score

    return similarities

