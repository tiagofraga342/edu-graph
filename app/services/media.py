import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import mimetypes
from PIL import Image
import aiofiles

# Configuration
MEDIA_ROOT = "/app/media"
ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.aac'],
    'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
    'archive': ['.zip', '.rar', '.7z', '.tar', '.gz']
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

class MediaService:
    def __init__(self):
        self.media_root = Path(MEDIA_ROOT)
        print(f"🔧 MediaService: Initializing with root: {self.media_root}")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = ['images', 'documents', 'audio', 'video', 'archives', 'thumbnails']
        print(f"🔧 MediaService: Creating directories in {self.media_root}")
        for directory in directories:
            dir_path = self.media_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created/verified directory: {dir_path}")
        print(f"🔧 MediaService: All directories ready")
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type based on extension"""
        ext = Path(filename).suffix.lower()
        for file_type, extensions in ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return 'unknown'
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return self.get_file_type(filename) != 'unknown'
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename while preserving extension"""
        ext = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{ext}"
    
    def get_file_path(self, file_type: str, filename: str) -> Path:
        """Get the full path for a file based on its type"""
        # Map file types to directory names
        type_to_dir = {
            'image': 'images',
            'document': 'documents',
            'audio': 'audio',
            'video': 'video',
            'archive': 'archives',
            'unknown': 'documents'  # Default fallback
        }
        directory = type_to_dir.get(file_type, 'documents')
        return self.media_root / directory / filename
    
    async def save_file(self, file_content: bytes, original_filename: str, note_id: str) -> Dict[str, Any]:
        """Save uploaded file and return metadata"""
        print(f"🔧 MediaService: Saving file {original_filename} for note {note_id}")
        print(f"🔧 File size: {len(file_content)} bytes")

        if not self.is_allowed_file(original_filename):
            print(f"❌ File type not allowed: {original_filename}")
            raise ValueError(f"File type not allowed: {original_filename}")

        if len(file_content) > MAX_FILE_SIZE:
            print(f"❌ File too large: {len(file_content)} bytes > {MAX_FILE_SIZE} bytes")
            raise ValueError(f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB")

        file_type = self.get_file_type(original_filename)
        unique_filename = self.generate_unique_filename(original_filename)
        file_path = self.get_file_path(file_type, unique_filename)

        print(f"🔧 File type: {file_type}")
        print(f"🔧 Unique filename: {unique_filename}")
        print(f"🔧 File path: {file_path}")

        # Save the file
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            print(f"✅ File saved successfully to {file_path}")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            raise
        
        # Generate metadata
        # Map file types to directory names for URL generation
        type_to_dir = {
            'image': 'images',
            'document': 'documents',
            'audio': 'audio',
            'video': 'video',
            'archive': 'archives',
            'unknown': 'documents'
        }
        directory = type_to_dir.get(file_type, 'documents')

        metadata = {
            'id': str(uuid.uuid4()),
            'original_filename': original_filename,
            'stored_filename': unique_filename,
            'file_type': file_type,
            'file_size': len(file_content),
            'mime_type': mimetypes.guess_type(original_filename)[0],
            'note_id': note_id,
            'file_path': str(file_path),
            'url': f"/media/{directory}/{unique_filename}"
        }

        print(f"🔧 Generated metadata: {metadata}")
        
        # Generate thumbnail for images
        if file_type == 'image':
            thumbnail_path = await self.generate_thumbnail(file_path, unique_filename)
            if thumbnail_path:
                metadata['thumbnail_url'] = f"/media/thumbnails/{Path(thumbnail_path).name}"
        
        return metadata
    
    async def generate_thumbnail(self, image_path: Path, filename: str) -> Optional[Path]:
        """Generate thumbnail for image files"""
        try:
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path = self.media_root / 'thumbnails' / thumbnail_filename
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None
    
    async def delete_file(self, metadata: Dict[str, Any]) -> bool:
        """Delete file and its thumbnail if exists"""
        try:
            file_path = Path(metadata['file_path'])
            if file_path.exists():
                file_path.unlink()
            
            # Delete thumbnail if exists
            if 'thumbnail_url' in metadata:
                thumbnail_path = self.media_root / 'thumbnails' / Path(metadata['thumbnail_url']).name
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
            
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def get_file_info(self, file_type: str, filename: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        file_path = self.get_file_path(file_type, filename)
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        return {
            'filename': filename,
            'file_type': file_type,
            'file_size': stat.st_size,
            'mime_type': mimetypes.guess_type(filename)[0],
            'file_path': str(file_path)
        }

# Global media service instance
media_service = MediaService()
