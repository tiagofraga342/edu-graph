from pymongo import MongoClient
import gridfs

client = MongoClient("mongodb://mongodb:27017/")  # use service name 'mongodb'
db = client["note_graph"]

notes_collection = db["notes"]
fs = gridfs.GridFS(db)
