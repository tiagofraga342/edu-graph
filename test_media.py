#!/usr/bin/env python3
"""
Enhanced test script for debugging media attachment functionality
"""
import requests
import json
import os
import sys
from pathlib import Path
import time

API_BASE_URL = "http://localhost:8000"

def debug_print(message):
    """Print debug message with timestamp"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def check_api_health():
    """Check if API is running and healthy"""
    debug_print("🔍 Checking API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            debug_print("✅ API is running")
            return True
        else:
            debug_print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        debug_print("❌ Cannot connect to API - is it running?")
        return False
    except requests.exceptions.Timeout:
        debug_print("❌ API request timed out")
        return False

def test_create_note():
    """Test creating a note"""
    debug_print("📝 Testing note creation...")

    data = {
        "title": "Test Note with Attachments",
        "content": "This is a test note that will have attachments."
    }

    try:
        response = requests.post(f"{API_BASE_URL}/notes", json=data, timeout=10)
        debug_print(f"Note creation response: {response.status_code}")

        if response.status_code == 200:
            note = response.json()
            debug_print(f"✅ Note created successfully: {note['id']}")
            return note['id']
        else:
            debug_print(f"❌ Failed to create note: {response.status_code}")
            debug_print(f"Response: {response.text}")
            return None
    except Exception as e:
        debug_print(f"❌ Exception during note creation: {e}")
        return None

def test_upload_attachment(note_id):
    """Test uploading an attachment"""
    debug_print("📎 Testing file upload...")

    # Create a test file
    test_file_path = Path("test_attachment.txt")
    test_content = "This is a test file for attachment upload.\nLine 2\nLine 3"

    debug_print(f"Creating test file: {test_file_path}")
    with open(test_file_path, "w") as f:
        f.write(test_content)

    try:
        debug_print(f"Uploading file to note {note_id}")
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_attachment.txt", f, "text/plain")}
            response = requests.post(
                f"{API_BASE_URL}/notes/{note_id}/attachments",
                files=files,
                timeout=30
            )

        debug_print(f"Upload response: {response.status_code}")

        if response.status_code == 200:
            attachment = response.json()
            debug_print(f"✅ File uploaded successfully: {attachment['id']}")
            debug_print(f"File details: {attachment.get('original_filename')} ({attachment.get('file_size')} bytes)")
            return attachment['id']
        else:
            debug_print(f"❌ Failed to upload file: {response.status_code}")
            debug_print(f"Response: {response.text}")
            return None

    except Exception as e:
        debug_print(f"❌ Exception during upload: {e}")
        return None

    finally:
        # Clean up test file
        if test_file_path.exists():
            test_file_path.unlink()
            debug_print("🧹 Cleaned up test file")

def test_get_note_with_attachments(note_id):
    """Test retrieving a note with attachments"""
    print("Testing note retrieval with attachments...")
    
    response = requests.get(f"{API_BASE_URL}/notes/{note_id}")
    if response.status_code == 200:
        note = response.json()
        print(f"✅ Note retrieved successfully")
        print(f"   Title: {note['title']}")
        print(f"   Attachments: {len(note.get('attachments', []))}")
        for att in note.get('attachments', []):
            print(f"     - {att['original_filename']} ({att['file_type']}, {att['file_size']} bytes)")
        return True
    else:
        print(f"❌ Failed to retrieve note: {response.status_code} - {response.text}")
        return False

def test_download_attachment(attachment_id):
    """Test downloading an attachment"""
    print("Testing file download...")
    
    response = requests.get(f"{API_BASE_URL}/attachments/{attachment_id}/download")
    if response.status_code == 200:
        print(f"✅ File downloaded successfully ({len(response.content)} bytes)")
        return True
    else:
        print(f"❌ Failed to download file: {response.status_code} - {response.text}")
        return False

def test_delete_attachment(attachment_id):
    """Test deleting an attachment"""
    print("Testing file deletion...")
    
    response = requests.delete(f"{API_BASE_URL}/attachments/{attachment_id}")
    if response.status_code == 200:
        print(f"✅ File deleted successfully")
        return True
    else:
        print(f"❌ Failed to delete file: {response.status_code} - {response.text}")
        return False

def test_media_directory():
    """Test if media directories are accessible"""
    debug_print("📁 Testing media directory access...")

    try:
        response = requests.get(f"{API_BASE_URL}/media/", timeout=5)
        debug_print(f"Media directory response: {response.status_code}")

        # Try to access a subdirectory
        response = requests.get(f"{API_BASE_URL}/media/images/", timeout=5)
        debug_print(f"Images directory response: {response.status_code}")

    except Exception as e:
        debug_print(f"❌ Error accessing media directories: {e}")

def test_cors_headers():
    """Test CORS headers"""
    debug_print("🌐 Testing CORS headers...")

    try:
        response = requests.options(f"{API_BASE_URL}/notes", timeout=5)
        debug_print(f"OPTIONS response: {response.status_code}")
        debug_print(f"CORS headers: {dict(response.headers)}")

    except Exception as e:
        debug_print(f"❌ Error testing CORS: {e}")

def main():
    debug_print("🧪 Enhanced Media Attachment Debugging")
    debug_print("=" * 50)

    # Check API health first
    if not check_api_health():
        debug_print("❌ API health check failed. Please start the application first.")
        sys.exit(1)

    # Test CORS and media directory access
    test_cors_headers()
    test_media_directory()

    # Run main tests
    note_id = test_create_note()
    if not note_id:
        debug_print("❌ Cannot proceed without a note. Exiting.")
        sys.exit(1)

    attachment_id = test_upload_attachment(note_id)
    if not attachment_id:
        debug_print("❌ Upload failed. Checking note without attachments...")
        test_get_note_with_attachments(note_id)
        sys.exit(1)

    test_get_note_with_attachments(note_id)
    test_download_attachment(attachment_id)
    test_delete_attachment(attachment_id)

    debug_print("\n🎉 All tests completed successfully!")

if __name__ == "__main__":
    main()
