from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
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
from services.linking import link_similar_notes, link_similar_notes_enhanced
from services.advanced_similarity import advanced_analyzer
from services.similarity_config import get_config, create_custom_config, CONFIGS
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

class SimilarityDetails(BaseModel):
    semantic: float
    keyword: float
    structural: float
    topic: float
    overall: float

class EnhancedSimilarNote(BaseModel):
    id: str
    score: float
    relationship_type: str
    details: SimilarityDetails

class RelationshipAnalysis(BaseModel):
    semantic: List[EnhancedSimilarNote]
    hierarchical: List[EnhancedSimilarNote]
    sequential: List[EnhancedSimilarNote]
    conceptual: List[EnhancedSimilarNote]
    weak: List[EnhancedSimilarNote]

class SimilarityConfigRequest(BaseModel):
    config_name: Optional[str] = 'default'
    semantic_weight: Optional[float] = None
    keyword_weight: Optional[float] = None
    structural_weight: Optional[float] = None
    topic_weight: Optional[float] = None
    min_threshold: Optional[float] = None

class LinkingResult(BaseModel):
    relationships_created: Dict[str, int]
    total_relationships: int
    config_used: str

@app.post("/notes", response_model=NoteResponse)
def create_new_note(note: NoteCreate, use_enhanced_linking: bool = True):
    embedding = get_embedding(note.content)
    data = {"title": note.title, "content": note.content, "embedding": embedding}
    new_note = create_note(data)
    create_note_node(new_note["id"])

    # Use enhanced linking by default
    if use_enhanced_linking:
        try:
            advanced_analyzer.create_smart_relationships(new_note["id"], embedding)
        except Exception as e:
            # Fallback to basic linking if enhanced fails
            print(f"Enhanced linking failed, using basic linking: {e}")
            link_similar_notes(new_note["id"], embedding)
    else:
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

@app.get("/notes/{note_id}/analyze", response_model=RelationshipAnalysis)
def analyze_note_relationships(note_id: str, config_name: str = 'default'):
    """
    Perform comprehensive relationship analysis for a note
    """
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    embedding = note.get('embedding', [])
    if not embedding:
        raise HTTPException(status_code=400, detail="Nota não possui embedding")

    try:
        # Get configuration
        config = get_config(config_name)

        # Perform analysis
        relationships = advanced_analyzer.analyze_note_relationships(
            note_id, embedding, advanced_analysis=True
        )

        # Convert to response format
        def convert_relationships(rel_list):
            return [
                EnhancedSimilarNote(
                    id=rel['note_id'],
                    score=rel['score'],
                    relationship_type=rel['type'],
                    details=SimilarityDetails(**rel.get('details', {
                        'semantic': 0, 'keyword': 0, 'structural': 0, 'topic': 0, 'overall': rel['score']
                    }))
                ) for rel in rel_list
            ]

        return RelationshipAnalysis(
            semantic=convert_relationships(relationships.get('semantic', [])),
            hierarchical=convert_relationships(relationships.get('hierarchical', [])),
            sequential=convert_relationships(relationships.get('sequential', [])),
            conceptual=convert_relationships(relationships.get('conceptual', [])),
            weak=convert_relationships(relationships.get('weak', []))
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@app.post("/notes/{note_id}/link-enhanced", response_model=LinkingResult)
def create_enhanced_links(note_id: str, config_request: SimilarityConfigRequest):
    """
    Create enhanced relationships using advanced similarity analysis
    """
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota não encontrada")

    embedding = note.get('embedding', [])
    if not embedding:
        raise HTTPException(status_code=400, detail="Nota não possui embedding")

    try:
        # Get or create configuration
        if config_request.config_name and config_request.config_name in CONFIGS:
            config = get_config(config_request.config_name)
            config_used = config_request.config_name
        else:
            # Create custom config from request parameters
            custom_params = {k: v for k, v in config_request.dict().items()
                           if v is not None and k != 'config_name'}
            config = create_custom_config(**custom_params)
            config_used = 'custom'

        # Create smart relationships
        relationship_counts = advanced_analyzer.create_smart_relationships(
            note_id,
            embedding,
            max_relationships_per_type=config.max_relationships_per_type
        )

        total_relationships = sum(relationship_counts.values())

        return LinkingResult(
            relationships_created=relationship_counts,
            total_relationships=total_relationships,
            config_used=config_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar relacionamentos: {str(e)}")

@app.get("/similarity/configs")
def list_similarity_configs():
    """List available similarity configurations"""
    return {
        "available_configs": list(CONFIGS.keys()),
        "default_config": "default",
        "config_descriptions": {
            "default": "Balanced approach with moderate thresholds",
            "semantic_focused": "Emphasizes semantic similarity from embeddings",
            "keyword_focused": "Emphasizes keyword and TF-IDF similarity",
            "strict": "High thresholds, fewer relationships",
            "permissive": "Lower thresholds, more relationships",
            "academic": "Optimized for academic/research content",
            "creative": "Optimized for creative/artistic content"
        }
    }

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