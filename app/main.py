from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4

from db.neo4j import create_note_node
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

# Modelo para receber dados JSON
class NoteRequest(BaseModel):
    title: str
    text: str

@app.post("/notes")
def add_note(note: NoteRequest):
    vec = embed(note.text)
    note_id = str(uuid4())
    create_note_node(note_id, note.title, vec)
    link_similar_notes(note_id, vec)
    return {"id": note_id, "title": note.title}