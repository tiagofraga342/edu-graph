from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from db.mongo import (
    create_note, get_note, get_all_notes,
    update_note, delete_note, notes_collection
)
from db.neo4j import (
    create_note_node, create_relationship, get_relationships, driver
)
from services.embedding import get_embedding
from services.similarity import cosine_similarity
from services.linking import link_similar_notes

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteResponse(BaseModel):
    id: str
    title: str
    content: str

class SimilarNote(BaseModel):
    id: str
    score: float

class Relationship(BaseModel):
    type: str
    id: str

@app.post("/notes", response_model=NoteResponse)
def create_new_note(note: NoteCreate):
    embedding = get_embedding(note.content)
    data = {"title": note.title, "content": note.content, "embedding": embedding}
    new_note = create_note(data)
    create_note_node(new_note["id"])
    link_similar_notes(new_note["id"], embedding)
    return new_note

@app.post("/notes/batch", response_model=List[NoteResponse])
def create_notes_batch(notes: List[NoteCreate]):
    created = []
    for note in notes:
        embedding = get_embedding(note.content)
        data = {"title": note.title, "content": note.content, "embedding": embedding}
        new = create_note(data)
        create_note_node(new["id"])
        link_similar_notes(new["id"], embedding)
        created.append(new)
    return created

@app.get("/notes", response_model=List[NoteResponse])
def list_notes():
    return get_all_notes()

@app.get("/notes/{note_id}", response_model=NoteResponse)
def read_note(note_id: str):
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return note

@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_existing_note(note_id: str, note: NoteCreate):
    existing = get_note(note_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    embedding = get_embedding(note.content)
    data = {"title": note.title, "content": note.content, "embedding": embedding}
    updated = update_note(note_id, data)
    return updated

@app.delete("/notes/{note_id}")
def delete_existing_note(note_id: str):
    if not get_note(note_id):
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    success = delete_note(note_id)
    return {"deleted": success}

@app.get("/notes/{note_id}/similar", response_model=List[SimilarNote])
def get_similar_notes(note_id: str, top_k: int = 5):
    notes = get_all_notes()
    target = next((n for n in notes if n["id"] == note_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    sims = []
    for n in notes:
        if n["id"] == note_id:
            continue
        score = cosine_similarity(target["embedding"], n["embedding"])
        sims.append({"id": n["id"], "score": float(score)})
    sims.sort(key=lambda x: x["score"], reverse=True)
    return sims[:top_k]

@app.post("/notes/{note_id}/relationships", response_model=Relationship)
def link_notes(note_id: str, target_id: str, rel_type: str = "RELATED"):
    # garante existência
    if not get_note(note_id) or not get_note(target_id):
        raise HTTPException(status_code=404, detail="Uma das notas não foi encontrada")
    create_relationship(note_id, target_id, rel_type)
    return {"type": rel_type, "id": target_id}

@app.get("/notes/{note_id}/relationships", response_model=List[Relationship])
def list_relationships(note_id: str):
    if not get_note(note_id):
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return get_relationships(note_id)

@app.get("/graph")
def get_graph():
    # 1) Busca todas as notas no Mongo
    notes = get_all_notes()  
    nodes = [{"id": n["id"], "label": n["title"]} for n in notes]

    # 2) Para cada nota, busca relacionamentos no Neo4j
    edges = []
    for note in notes:
        rels = get_relationships(note["id"])
        for r in rels:
            edges.append({
                "from": note["id"],
                "to": r["id"],
            })

    return {"nodes": nodes, "edges": edges}


@app.delete("/notes")
def delete_all_notes():
    res = notes_collection.delete_many({})
    with driver.session() as session:
        session.run("MATCH (n:Note) DETACH DELETE n")
    return {"deleted_mongo": res.deleted_count, "deleted_neo4j": "all Note nodes"}