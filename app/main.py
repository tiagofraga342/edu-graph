from fastapi import FastAPI
from uuid import uuid4
from app.db.neo4j import create_note_node
from app.services.embedding import embed

app = FastAPI()

@app.post("/notes")
def add_note(title: str, text: str):
    vec = embed(text)
    note_id = str(uuid4())
    create_note_node(note_id, title, vec)
    return {"id": note_id, "title": title}

