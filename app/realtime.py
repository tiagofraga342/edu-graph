from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime
import uuid

class ConnectionManager:
    def __init__(self):
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []
        # Map note_id to set of connected clients
        self.note_subscribers: Dict[str, Set[WebSocket]] = {}
        # Map websocket to user info
        self.connection_info: Dict[WebSocket, dict] = {}
        # Active editing sessions (note_id -> user_id)
        self.active_editors: Dict[str, str] = {}
        # Pending changes for conflict resolution
        self.pending_changes: Dict[str, List[dict]] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id or str(uuid.uuid4()),
            "connected_at": datetime.now()
        }

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from note subscriptions
        for note_id, subscribers in self.note_subscribers.items():
            subscribers.discard(websocket)
        
        # Remove from active editors
        user_id = self.connection_info.get(websocket, {}).get("user_id")
        if user_id:
            notes_to_release = [note_id for note_id, editor_id in self.active_editors.items() if editor_id == user_id]
            for note_id in notes_to_release:
                del self.active_editors[note_id]
        
        # Clean up connection info
        if websocket in self.connection_info:
            del self.connection_info[websocket]

    async def subscribe_to_note(self, websocket: WebSocket, note_id: str):
        if note_id not in self.note_subscribers:
            self.note_subscribers[note_id] = set()
        self.note_subscribers[note_id].add(websocket)
        
        # Notify about current editor if any
        if note_id in self.active_editors:
            await self.send_personal_message(websocket, {
                "type": "editor_status",
                "note_id": note_id,
                "editor_id": self.active_editors[note_id],
                "is_editing": True
            })

    async def unsubscribe_from_note(self, websocket: WebSocket, note_id: str):
        if note_id in self.note_subscribers:
            self.note_subscribers[note_id].discard(websocket)
            if not self.note_subscribers[note_id]:
                del self.note_subscribers[note_id]

    async def start_editing(self, websocket: WebSocket, note_id: str):
        user_id = self.connection_info.get(websocket, {}).get("user_id")
        if not user_id:
            return False
        
        # Check if someone else is already editing
        if note_id in self.active_editors and self.active_editors[note_id] != user_id:
            await self.send_personal_message(websocket, {
                "type": "edit_denied",
                "note_id": note_id,
                "reason": "Another user is currently editing this note",
                "current_editor": self.active_editors[note_id]
            })
            return False
        
        # Grant editing permission
        self.active_editors[note_id] = user_id
        
        # Notify all subscribers about the new editor
        await self.broadcast_to_note(note_id, {
            "type": "editor_status",
            "note_id": note_id,
            "editor_id": user_id,
            "is_editing": True
        }, exclude=websocket)
        
        return True

    async def stop_editing(self, websocket: WebSocket, note_id: str):
        user_id = self.connection_info.get(websocket, {}).get("user_id")
        if note_id in self.active_editors and self.active_editors[note_id] == user_id:
            del self.active_editors[note_id]
            
            # Notify all subscribers that editing stopped
            await self.broadcast_to_note(note_id, {
                "type": "editor_status",
                "note_id": note_id,
                "editor_id": None,
                "is_editing": False
            })

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # Connection might be closed
            pass

    async def broadcast_to_note(self, note_id: str, message: dict, exclude: WebSocket = None):
        if note_id not in self.note_subscribers:
            return
        
        disconnected = []
        for websocket in self.note_subscribers[note_id]:
            if websocket == exclude:
                continue
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_change(self, note_id: str, change_data: dict, sender: WebSocket = None):
        """Broadcast real-time changes to all subscribers of a note"""
        message = {
            "type": "note_change",
            "note_id": note_id,
            "change": change_data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_note(note_id, message, exclude=sender)

    async def handle_text_change(self, websocket: WebSocket, note_id: str, change_data: dict):
        """Handle real-time text changes with operational transformation"""
        user_id = self.connection_info.get(websocket, {}).get("user_id")
        
        # Verify user has editing permission
        if note_id not in self.active_editors or self.active_editors[note_id] != user_id:
            await self.send_personal_message(websocket, {
                "type": "error",
                "message": "You don't have permission to edit this note"
            })
            return
        
        # Add metadata to change
        change_data.update({
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Broadcast to other clients
        await self.broadcast_change(note_id, change_data, sender=websocket)

# Global connection manager instance
manager = ConnectionManager()
