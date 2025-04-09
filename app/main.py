from fastapi import FastAPI
from uuid import uuid4

from db.neo4j import create_note_node
from services.embedding import embed
from services.linking import link_similar_notes

app = FastAPI()

@app.post("/notes")
def add_note(title: str, text: str):
    vec = embed(text)
    note_id = str(uuid4())
    create_note_node(note_id, title, vec)
    link_similar_notes(note_id, vec)
    return {"id": note_id, "title": title}

