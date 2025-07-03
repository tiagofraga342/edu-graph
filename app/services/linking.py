# linking.py
from db.mongo import get_all_notes, get_note          # pega notas + embeddings do Mongo
from db.neo4j import create_relationship    # cria as arestas no Neo4j
from services.similarity import (
    cosine_similarity,
    calculate_comprehensive_similarity
)
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_relationship_type(similarities: Dict[str, float]) -> Optional[str]:
    """
    Determine the type of relationship based on similarity scores

    Returns:
        - "HIGHLY_RELATED" for very similar content (>= 0.8)
        - "SEMANTICALLY_RELATED" for semantic similarity (>= 0.7)
        - "TOPICALLY_RELATED" for topic similarity (>= 0.6)
        - "STRUCTURALLY_RELATED" for structural similarity (>= 0.6)
        - "LOOSELY_RELATED" for weak but meaningful connections (>= 0.5)
        - None for no meaningful relationship
    """
    overall = similarities.get('overall', 0.0)
    semantic = similarities.get('semantic', 0.0)
    topic = similarities.get('topic', 0.0)
    structural = similarities.get('structural', 0.0)
    keyword = similarities.get('keyword', 0.0)

    if overall >= 0.8:
        return "HIGHLY_RELATED"
    elif semantic >= 0.7:
        return "SEMANTICALLY_RELATED"
    elif topic >= 0.6:
        return "TOPICALLY_RELATED"
    elif structural >= 0.6:
        return "STRUCTURALLY_RELATED"
    elif keyword >= 0.6:
        return "KEYWORD_RELATED"
    elif overall >= 0.5:
        return "LOOSELY_RELATED"
    else:
        return None

def link_similar_notes_enhanced(
    new_note_id: str,
    new_embedding: List[float],
    similarity_weights: Optional[Dict[str, float]] = None,
    min_overall_threshold: float = 0.5
) -> Dict[str, int]:
    """
    Enhanced note linking with multiple similarity measures and relationship types

    Args:
        new_note_id: ID of the new note
        new_embedding: Pre-computed embedding of the new note
        similarity_weights: Optional custom weights for similarity calculation
        min_overall_threshold: Minimum overall similarity to create any relationship

    Returns:
        Dictionary with counts of each relationship type created
    """
    # Get the new note's content
    new_note = get_note(new_note_id)
    if not new_note:
        logger.error(f"Could not find note with ID: {new_note_id}")
        return {}

    new_content = new_note.get('content', '')
    existing_notes = get_all_notes()

    relationship_counts = {}

    for note in existing_notes:
        if note["id"] == new_note_id:
            continue

        try:
            # Calculate comprehensive similarity
            similarities = calculate_comprehensive_similarity(
                new_content,
                note.get('content', ''),
                new_embedding,
                note.get('embedding', []),
                weights=similarity_weights
            )

            # Determine relationship type
            rel_type = determine_relationship_type(similarities)

            if rel_type and similarities['overall'] >= min_overall_threshold:
                # Create bidirectional relationships
                create_relationship(new_note_id, note["id"], rel_type=rel_type)
                create_relationship(note["id"], new_note_id, rel_type=rel_type)

                # Track relationship counts
                relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1

                logger.info(f"Created {rel_type} relationship between {new_note_id} and {note['id']} "
                           f"(overall: {similarities['overall']:.3f})")

        except Exception as e:
            logger.error(f"Error processing similarity for note {note['id']}: {e}")
            continue

    return relationship_counts

def link_similar_notes(new_note_id: str, new_vec: list, threshold: float = 0.55):
    """
    Legacy function for backward compatibility
    Now uses enhanced linking with default settings
    """
    return link_similar_notes_enhanced(
        new_note_id,
        new_vec,
        min_overall_threshold=threshold
    )
