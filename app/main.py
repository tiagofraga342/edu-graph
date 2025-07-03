from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os

from db.mongo import (
    create_note, get_note, get_all_notes,
    update_note, delete_note, notes_collection,
    create_attachment, get_attachment, get_note_attachments,
    delete_attachment, delete_note_attachments, attachments_collection
)
from db.neo4j import (
    create_note_node, create_relationship, get_relationships, driver,
    find_shortest_path, find_all_paths, get_node_neighbors
)
from services.embedding import get_embedding
from services.similarity import cosine_similarity
from services.linking import link_similar_notes
from services.media import media_service
from realtime import manager

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

# Mount static files for media serving
os.makedirs("/app/media", exist_ok=True)
app.mount("/media", StaticFiles(directory="/app/media"), name="media")

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteUpdate(BaseModel):
    title: str = None
    content: str = None

class AttachmentResponse(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str]
    note_id: str
    url: str
    thumbnail_url: Optional[str] = None

class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    attachments: Optional[List[AttachmentResponse]] = []

class SimilarNote(BaseModel):
    id: str
    score: float

class Relationship(BaseModel):
    type: str
    id: str

class PathInfo(BaseModel):
    node_ids: List[str]
    relationship_types: List[str]
    length: int

class PathResponse(BaseModel):
    path: Optional[PathInfo]
    error: Optional[str]

class MultiplePathsResponse(BaseModel):
    paths: List[PathInfo]
    count: int
    error: Optional[str]

class NeighborInfo(BaseModel):
    id: str
    distance: int
    path: List[str]

class NeighborsResponse(BaseModel):
    neighbors: List[NeighborInfo]
    count: int

class ManualLinkRequest(BaseModel):
    target_note_id: str
    relationship_type: str = "RELATED"
    bidirectional: bool = True
    description: Optional[str] = None

class ManualLinkResponse(BaseModel):
    success: bool
    message: str
    relationship: Dict[str, str]
    bidirectional: bool

class DeleteRelationshipRequest(BaseModel):
    target_note_id: str
    relationship_type: Optional[str] = None
    bidirectional: bool = True

class AvailableNotesResponse(BaseModel):
    notes: List[Dict[str, str]]  # id, title
    total: int
    exclude_existing_relationships: bool

class SemanticSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    min_similarity: float = 0.3

class SemanticSearchResult(BaseModel):
    id: str
    title: str
    content: str
    similarity_score: float
    snippet: str  # Relevant excerpt from content

class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticSearchResult]
    total_results: int
    search_time_ms: float

class RelationshipInfo(BaseModel):
    id: str
    title: str
    relationship_type: str
    bidirectional: bool
    created_manually: bool = True

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
    notes = get_all_notes()
    for note in notes:
        note['attachments'] = get_note_attachments(note['id'])
    return notes

@app.get("/notes/{note_id}", response_model=NoteResponse)
def read_note(note_id: str):
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    note['attachments'] = get_note_attachments(note_id)
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

@app.patch("/notes/{note_id}", response_model=NoteResponse)
async def patch_existing_note(note_id: str, note: NoteUpdate):
    existing = get_note(note_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    # Build update data with only provided fields
    update_data = {}
    if note.title is not None:
        update_data["title"] = note.title
    if note.content is not None:
        update_data["content"] = note.content
        # Only recalculate embedding if content changed
        update_data["embedding"] = get_embedding(note.content)

    if not update_data:
        return existing

    updated = update_note(note_id, update_data)

    # Broadcast the update to WebSocket clients
    await manager.broadcast_to_note(note_id, {
        "type": "note_updated",
        "note_id": note_id,
        "note": updated,
        "updated_fields": list(update_data.keys())
    })

    return updated

@app.delete("/notes/{note_id}")
async def delete_existing_note(note_id: str):
    if not get_note(note_id):
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    # Delete all attachments for this note
    attachments = get_note_attachments(note_id)
    for attachment in attachments:
        await media_service.delete_file(attachment)
        delete_attachment(attachment['id'])

    success = delete_note(note_id)
    return {"deleted": success}


@app.delete("/notes")
async def delete_all_notes():
    """Delete all notes from both MongoDB and Neo4j"""
    try:
        # Get all notes first to delete their attachments
        all_notes = get_all_notes()

        # Delete all attachments
        attachment_count = 0
        for note in all_notes:
            attachments = get_note_attachments(note['id'])
            for attachment in attachments:
                await media_service.delete_file(attachment)
                delete_attachment(attachment['id'])
                attachment_count += 1

        # Delete all notes from MongoDB
        mongo_result = notes_collection.delete_many({})
        deleted_mongo = mongo_result.deleted_count

        # Delete all attachments metadata
        attachments_collection.delete_many({})

        # Delete all nodes from Neo4j
        with driver.session() as session:
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
            record = result.single()
            deleted_neo4j = record["deleted"] if record else 0

        return {
            "deleted_mongo": deleted_mongo,
            "deleted_neo4j": deleted_neo4j,
            "deleted_attachments": attachment_count,
            "message": f"Deleted {deleted_mongo} notes, {deleted_neo4j} Neo4j nodes, and {attachment_count} attachments"
        }

    except Exception as e:
        print(f"❌ Error deleting all notes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao deletar todas as notas: {str(e)}")

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

@app.post("/search/semantic", response_model=SemanticSearchResponse)
def semantic_search(search_request: SemanticSearchRequest):
    """
    Perform semantic search across all notes using embeddings
    """
    import time
    start_time = time.time()

    try:
        # Generate embedding for the search query
        query_embedding = get_embedding(search_request.query)

        # Get all notes with embeddings
        all_notes = get_all_notes()

        # Calculate similarity scores
        search_results = []
        for note in all_notes:
            if not note.get('embedding'):
                continue  # Skip notes without embeddings

            similarity = cosine_similarity(query_embedding, note['embedding'])

            if similarity >= search_request.min_similarity:
                # Generate snippet (relevant excerpt)
                snippet = generate_snippet(note['content'], search_request.query)

                search_results.append(SemanticSearchResult(
                    id=note['id'],
                    title=note['title'],
                    content=note['content'],
                    similarity_score=float(similarity),
                    snippet=snippet
                ))

        # Sort by similarity score (highest first)
        search_results.sort(key=lambda x: x.similarity_score, reverse=True)

        # Limit results
        limited_results = search_results[:search_request.max_results]

        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return SemanticSearchResponse(
            query=search_request.query,
            results=limited_results,
            total_results=len(search_results),
            search_time_ms=round(search_time, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca semântica: {str(e)}")

def generate_snippet(content: str, query: str, max_length: int = 200) -> str:
    """
    Generate a relevant snippet from content based on the query
    """
    import re

    # Simple snippet generation - find sentences containing query words
    query_words = query.lower().split()
    sentences = re.split(r'[.!?]+', content)

    # Score sentences based on query word presence
    scored_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        score = 0
        sentence_lower = sentence.lower()
        for word in query_words:
            if word in sentence_lower:
                score += 1

        if score > 0:
            scored_sentences.append((score, sentence))

    if scored_sentences:
        # Get the highest scoring sentence
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        best_sentence = scored_sentences[0][1]

        # Truncate if too long
        if len(best_sentence) > max_length:
            return best_sentence[:max_length] + "..."
        return best_sentence

    # Fallback: return first part of content
    if len(content) > max_length:
        return content[:max_length] + "..."
    return content

@app.get("/search/semantic", response_model=SemanticSearchResponse)
def semantic_search_get(q: str, max_results: int = 10, min_similarity: float = 0.3):
    """
    GET endpoint for semantic search (for easier testing and URL sharing)
    """
    search_request = SemanticSearchRequest(
        query=q,
        max_results=max_results,
        min_similarity=min_similarity
    )
    return semantic_search(search_request)

@app.post("/notes/{note_id}/relationships", response_model=Relationship)
def link_notes(note_id: str, target_id: str, rel_type: str = "RELATED"):
    """Legacy endpoint for backward compatibility"""
    # garante existência
    if not get_note(note_id) or not get_note(target_id):
        raise HTTPException(status_code=404, detail="Uma das notas não foi encontrada")
    create_relationship(note_id, target_id, rel_type)
    return {"type": rel_type, "id": target_id}

@app.post("/notes/{note_id}/link", response_model=ManualLinkResponse)
def create_manual_link(note_id: str, link_request: ManualLinkRequest):
    """
    Create a manual relationship between two notes
    """
    # Validate both notes exist
    source_note = get_note(note_id)
    target_note = get_note(link_request.target_note_id)

    if not source_note:
        raise HTTPException(status_code=404, detail="Nota de origem não encontrada")
    if not target_note:
        raise HTTPException(status_code=404, detail="Nota de destino não encontrada")

    if note_id == link_request.target_note_id:
        raise HTTPException(status_code=400, detail="Uma nota não pode se relacionar consigo mesma")

    try:
        # Create the primary relationship
        create_relationship(note_id, link_request.target_note_id, link_request.relationship_type)

        # Create bidirectional relationship if requested
        if link_request.bidirectional:
            create_relationship(link_request.target_note_id, note_id, link_request.relationship_type)

        return ManualLinkResponse(
            success=True,
            message=f"Relacionamento '{link_request.relationship_type}' criado com sucesso",
            relationship={
                "from": note_id,
                "to": link_request.target_note_id,
                "type": link_request.relationship_type
            },
            bidirectional=link_request.bidirectional
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar relacionamento: {str(e)}")

@app.delete("/notes/{note_id}/relationships/{target_note_id}")
def delete_manual_relationship(note_id: str, target_note_id: str, bidirectional: bool = True):
    """
    Delete a relationship between two notes
    """
    # Validate both notes exist
    if not get_note(note_id) or not get_note(target_note_id):
        raise HTTPException(status_code=404, detail="Uma das notas não foi encontrada")

    try:
        # Delete the primary relationship
        with driver.session() as session:
            session.run(
                "MATCH (a:Note {id: $from_id})-[r]->(b:Note {id: $to_id}) DELETE r",
                from_id=note_id,
                to_id=target_note_id
            )

            # Delete bidirectional relationship if requested
            if bidirectional:
                session.run(
                    "MATCH (a:Note {id: $from_id})-[r]->(b:Note {id: $to_id}) DELETE r",
                    from_id=target_note_id,
                    to_id=note_id
                )

        return {"success": True, "message": "Relacionamento removido com sucesso"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover relacionamento: {str(e)}")

@app.get("/notes/{note_id}/relationships", response_model=List[Relationship])
def list_relationships(note_id: str):
    if not get_note(note_id):
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return get_relationships(note_id)

@app.get("/notes/{note_id}/available-links", response_model=AvailableNotesResponse)
def get_available_notes_for_linking(note_id: str, exclude_existing: bool = True):
    """
    Get list of notes that can be linked to the specified note
    """
    if not get_note(note_id):
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    try:
        all_notes = get_all_notes()
        available_notes = []

        # Get existing relationships if we need to exclude them
        existing_relationships = set()
        if exclude_existing:
            relationships = get_relationships(note_id)
            existing_relationships = {rel["id"] for rel in relationships}

        for note in all_notes:
            # Skip the note itself
            if note["id"] == note_id:
                continue

            # Skip notes that already have relationships if requested
            if exclude_existing and note["id"] in existing_relationships:
                continue

            available_notes.append({
                "id": note["id"],
                "title": note["title"]
            })

        return AvailableNotesResponse(
            notes=available_notes,
            total=len(available_notes),
            exclude_existing_relationships=exclude_existing
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar notas disponíveis: {str(e)}")

@app.get("/notes/{note_id}/relationships/detailed", response_model=List[RelationshipInfo])
def get_detailed_relationships(note_id: str):
    """
    Get detailed information about relationships including note titles
    """
    if not get_note(note_id):
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    try:
        relationships = get_relationships(note_id)
        detailed_relationships = []

        for rel in relationships:
            related_note = get_note(rel["id"])
            if related_note:
                detailed_relationships.append(RelationshipInfo(
                    id=rel["id"],
                    title=related_note["title"],
                    relationship_type=rel["type"],
                    bidirectional=True,  # We'll assume bidirectional for now
                    created_manually=True
                ))

        return detailed_relationships

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar relacionamentos detalhados: {str(e)}")

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


# Neo4j health check endpoint
@app.get("/neo4j/health")
def check_neo4j_health():
    """Check Neo4j connection and basic stats"""
    try:
        with driver.session() as session:
            # Test connection
            result = session.run("RETURN 1 as test")
            record = result.single()
            if not record or record["test"] != 1:
                return {"status": "error", "message": "Neo4j connection failed"}

            # Get node counts
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()["total_nodes"]

            result = session.run("MATCH (n:Note) RETURN count(n) as note_nodes")
            note_nodes = result.single()["note_nodes"]

            result = session.run("MATCH ()-[r]->() RETURN count(r) as total_rels")
            total_rels = result.single()["total_rels"]

            return {
                "status": "healthy",
                "total_nodes": total_nodes,
                "note_nodes": note_nodes,
                "total_relationships": total_rels
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Path finding endpoints
@app.get("/notes/{start_note_id}/path-to/{end_note_id}", response_model=PathResponse)
def get_shortest_path(start_note_id: str, end_note_id: str, max_depth: int = 6):
    """Find the shortest path between two notes"""
    print(f"🔧 Path finding: start={start_note_id}, end={end_note_id}, max_depth={max_depth}")

    # Verify both notes exist
    start_note = get_note(start_note_id)
    end_note = get_note(end_note_id)

    print(f"🔧 Start note found: {start_note is not None}")
    print(f"🔧 End note found: {end_note is not None}")

    if not start_note:
        print(f"❌ Start note not found: {start_note_id}")
        raise HTTPException(status_code=404, detail="Nota de origem não encontrada")
    if not end_note:
        print(f"❌ End note not found: {end_note_id}")
        raise HTTPException(status_code=404, detail="Nota de destino não encontrada")

    if start_note_id == end_note_id:
        print(f"❌ Same note IDs provided")
        raise HTTPException(status_code=400, detail="As notas de origem e destino devem ser diferentes")

    try:
        print(f"🔧 Calling find_shortest_path...")
        result = find_shortest_path(start_note_id, end_note_id, max_depth)
        print(f"✅ Path finding result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error in path finding: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar caminho: {str(e)}")


@app.get("/notes/{start_note_id}/all-paths-to/{end_note_id}", response_model=MultiplePathsResponse)
def get_all_paths(start_note_id: str, end_note_id: str, max_depth: int = 4, max_paths: int = 5):
    """Find multiple paths between two notes"""
    print(f"🔧 All paths: start={start_note_id}, end={end_note_id}, max_depth={max_depth}, max_paths={max_paths}")

    # Verify both notes exist
    start_note = get_note(start_note_id)
    end_note = get_note(end_note_id)

    if not start_note:
        print(f"❌ Start note not found: {start_note_id}")
        raise HTTPException(status_code=404, detail="Nota de origem não encontrada")
    if not end_note:
        print(f"❌ End note not found: {end_note_id}")
        raise HTTPException(status_code=404, detail="Nota de destino não encontrada")

    if start_note_id == end_note_id:
        print(f"❌ Same note IDs provided")
        raise HTTPException(status_code=400, detail="As notas de origem e destino devem ser diferentes")

    try:
        print(f"🔧 Calling find_all_paths...")
        result = find_all_paths(start_note_id, end_note_id, max_depth, max_paths)
        print(f"✅ All paths result: {result}")
        return result
    except Exception as e:
        print(f"❌ Error in all paths: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar caminhos: {str(e)}")


@app.get("/notes/{note_id}/neighbors", response_model=NeighborsResponse)
def get_neighbors(note_id: str, depth: int = 1):
    """Get neighboring notes within specified depth"""
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    if depth < 1 or depth > 5:
        raise HTTPException(status_code=400, detail="Profundidade deve estar entre 1 e 5")

    try:
        result = get_node_neighbors(note_id, depth)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar vizinhos: {str(e)}")


# Media attachment endpoints
@app.post("/notes/{note_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(note_id: str, file: UploadFile = File(...)):
    print(f"🔧 Upload endpoint called for note {note_id}")
    print(f"🔧 File: {file.filename}, Content-Type: {file.content_type}, Size: {file.size}")

    # Verify note exists
    note = get_note(note_id)
    if not note:
        print(f"❌ Note {note_id} not found")
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    try:
        # Read file content
        file_content = await file.read()
        print(f"🔧 Read {len(file_content)} bytes from uploaded file")

        # Save file using media service
        metadata = await media_service.save_file(file_content, file.filename, note_id)
        print(f"🔧 Media service returned metadata: {metadata}")

        # Store metadata in MongoDB
        attachment = create_attachment(metadata)
        print(f"✅ Attachment created in MongoDB: {attachment}")

        return attachment

    except ValueError as e:
        print(f"❌ ValueError in upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Exception in upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")


@app.get("/notes/{note_id}/attachments", response_model=List[AttachmentResponse])
def get_attachments(note_id: str):
    # Verify note exists
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    return get_note_attachments(note_id)


@app.delete("/attachments/{attachment_id}")
async def delete_attachment_endpoint(attachment_id: str):
    attachment = get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")

    # Delete file from storage
    success = await media_service.delete_file(attachment)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao deletar arquivo")

    # Delete metadata from database
    db_success = delete_attachment(attachment_id)
    if not db_success:
        raise HTTPException(status_code=500, detail="Erro ao deletar metadados")

    return {"deleted": True}


@app.get("/attachments/{attachment_id}/download")
async def download_attachment(attachment_id: str):
    attachment = get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")

    file_path = attachment['file_path']
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no sistema")

    return FileResponse(
        path=file_path,
        filename=attachment['original_filename'],
        media_type=attachment['mime_type']
    )


@app.delete("/notes")
def delete_all_notes():
    res = notes_collection.delete_many({})
    with driver.session() as session:
        session.run("MATCH (n:Note) DETACH DELETE n")
    return {"deleted_mongo": res.deleted_count, "deleted_neo4j": "all Note nodes"}


# WebSocket endpoints for real-time editing
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")
            note_id = message.get("note_id")

            if message_type == "subscribe":
                await manager.subscribe_to_note(websocket, note_id)
                await manager.send_personal_message(websocket, {
                    "type": "subscribed",
                    "note_id": note_id
                })

            elif message_type == "unsubscribe":
                await manager.unsubscribe_from_note(websocket, note_id)

            elif message_type == "start_editing":
                success = await manager.start_editing(websocket, note_id)
                await manager.send_personal_message(websocket, {
                    "type": "edit_permission",
                    "note_id": note_id,
                    "granted": success
                })

            elif message_type == "stop_editing":
                await manager.stop_editing(websocket, note_id)

            elif message_type == "text_change":
                await manager.handle_text_change(websocket, note_id, message.get("change", {}))

            elif message_type == "save_note":
                # Handle auto-save
                change_data = message.get("data", {})
                if note_id and change_data:
                    # Update the note in the database
                    embedding = get_embedding(change_data.get("content", ""))
                    data = {
                        "title": change_data.get("title", ""),
                        "content": change_data.get("content", ""),
                        "embedding": embedding
                    }
                    updated_note = update_note(note_id, data)

                    # Broadcast save confirmation
                    await manager.broadcast_to_note(note_id, {
                        "type": "note_saved",
                        "note_id": note_id,
                        "note": updated_note
                    })

    except WebSocketDisconnect:
        manager.disconnect(websocket)