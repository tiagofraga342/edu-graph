# linking.py
from db.mongo import get_all_notes          # pega notas + embeddings do Mongo
from db.neo4j import create_relationship    # cria as arestas no Neo4j
from services.similarity import cosine_similarity

def link_similar_notes(new_note_id: str, new_vec: list, threshold: float = 0.75):
    existing_notes = get_all_notes()
    for note in existing_notes:
        if note["id"] == new_note_id:
            continue
        sim = cosine_similarity(new_vec, note["embedding"])
        if sim >= threshold:
            # criamos relações bidirecionais (opcional)
            create_relationship(new_note_id, note["id"], rel_type="SIMILAR")
            create_relationship(note["id"], new_note_id, rel_type="SIMILAR")
