from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from typing import List, Dict, Any

MONGO_URI = "mongodb://mongodb:27017"
client = MongoClient(MONGO_URI)
db = client["edu_graph"]
notes_collection = db["notes"]
attachments_collection = db["attachments"]

def create_note(data: dict) -> dict:
    """
    data: { title: str, content: str, embedding: List[float] }
    """
    res = notes_collection.insert_one(data)
    note = notes_collection.find_one({"_id": res.inserted_id})
    note["id"] = str(note.pop("_id"))
    return note


def get_note(note_id: str) -> dict:
    note = notes_collection.find_one({"_id": ObjectId(note_id)})
    if note:
        note["id"] = str(note.pop("_id"))
    return note


def get_all_notes() -> list:
    notes = []
    for note in notes_collection.find():
        note["id"] = str(note.pop("_id"))
        notes.append(note)
    return notes


def update_note(note_id: str, data: dict) -> dict:
    notes_collection.update_one({"_id": ObjectId(note_id)}, {"$set": data})
    return get_note(note_id)


def delete_note(note_id: str) -> bool:
    res = notes_collection.delete_one({"_id": ObjectId(note_id)})
    return res.deleted_count == 1


# Attachment functions
def create_attachment(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an attachment record
    data: { id: str, original_filename: str, stored_filename: str, file_type: str,
            file_size: int, mime_type: str, note_id: str, file_path: str, url: str,
            thumbnail_url?: str }
    """
    print(f"🔧 MongoDB: Creating attachment with data: {data}")
    try:
        res = attachments_collection.insert_one(data)
        attachment = attachments_collection.find_one({"_id": res.inserted_id})
        attachment["_id"] = str(attachment.pop("_id"))
        print(f"✅ MongoDB: Attachment created successfully: {attachment}")
        return attachment
    except Exception as e:
        print(f"❌ MongoDB: Error creating attachment: {e}")
        raise


def get_attachment(attachment_id: str) -> Dict[str, Any]:
    """Get attachment by ID"""
    attachment = attachments_collection.find_one({"id": attachment_id})
    if attachment:
        attachment["_id"] = str(attachment.pop("_id"))
    return attachment


def get_note_attachments(note_id: str) -> List[Dict[str, Any]]:
    """Get all attachments for a specific note"""
    attachments = []
    for attachment in attachments_collection.find({"note_id": note_id}):
        attachment["_id"] = str(attachment.pop("_id"))
        attachments.append(attachment)
    return attachments


def delete_attachment(attachment_id: str) -> bool:
    """Delete an attachment record"""
    res = attachments_collection.delete_one({"id": attachment_id})
    return res.deleted_count == 1


def delete_note_attachments(note_id: str) -> int:
    """Delete all attachments for a note"""
    res = attachments_collection.delete_many({"note_id": note_id})
    return res.deleted_count