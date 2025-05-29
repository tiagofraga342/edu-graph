from pymongo import MongoClient
from bson.objectid import ObjectId
import os

MONGO_URI = "mongodb://mongodb:27017"
client = MongoClient(MONGO_URI)
db = client["edu_graph"]
notes_collection = db["notes"]

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