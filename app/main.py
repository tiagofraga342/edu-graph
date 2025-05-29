from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from typing import List
from pydantic import BaseModel
from uuid import uuid4

from db.neo4j import create_note_node, get_all_notes, get_all_notes_with_embeddings
from services.similarity import cosine_similarity
from services.embedding import embed
from services.linking import link_similar_notes

app = FastAPI()

# CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoteRequest(BaseModel):
    title: str
    text: str

class NoteResponse(BaseModel):
    id: str
    title: str

@app.post("/notes")
def add_note(note: NoteRequest):
    vec = embed(note.text)
    note_id = str(uuid4())
    create_note_node(note_id, note.title, vec)
    link_similar_notes(note_id, vec)
    return {"id": note_id, "title": note.title}

@app.get("/notes", response_model=List[NoteResponse])
def list_notes():
    """
    Retorna todas as notas cadastradas (apenas id e título).
    """
    return get_all_notes()

@app.get("/notes/{note_id}/similar", response_model=List[dict])
def get_similar_notes(note_id: str, top_k: int = 5):
    """
    Retorna as top_k notas mais similares à nota note_id.
    """

    notes = get_all_notes_with_embeddings()

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