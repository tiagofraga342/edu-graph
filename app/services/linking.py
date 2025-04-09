from db.neo4j import get_all_notes_with_embeddings, create_similarity_edge
from services.similarity import cosine_similarity

def link_similar_notes(new_note_id: str, new_vec: list, threshold: float = 0.75):
    existing_notes = get_all_notes_with_embeddings()
    for note in existing_notes:
        if note["id"] == new_note_id:
            continue
        sim = cosine_similarity(new_vec, note["embedding"])
        if sim >= threshold:
            create_similarity_edge(new_note_id, note["id"], float(sim))

