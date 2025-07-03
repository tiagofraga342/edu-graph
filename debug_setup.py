#!/usr/bin/env python3
"""
Debug script to check the application setup
"""
import requests
import time
import sys

API_BASE_URL = "http://localhost:8000"

def check_api_endpoints():
    """Check various API endpoints"""
    endpoints = [
        ("/docs", "API Documentation"),
        ("/notes", "Notes endpoint"),
        ("/media/", "Media static files"),
    ]
    
    print("🔍 Checking API endpoints...")
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: Error - {e}")

def test_note_creation():
    """Test basic note creation"""
    print("\n📝 Testing note creation...")
    try:
        data = {"title": "Debug Test Note", "content": "This is a debug test note."}
        response = requests.post(f"{API_BASE_URL}/notes", json=data, timeout=10)
        
        if response.status_code == 200:
            note = response.json()
            print(f"✅ Note created: {note['id']}")
            return note['id']
        else:
            print(f"❌ Note creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Note creation error: {e}")
        return None

def test_file_upload(note_id):
    """Test file upload functionality"""
    print(f"\n📎 Testing file upload to note {note_id}...")
    
    # Create a simple test file
    test_content = b"This is a test file for debugging media attachments."
    
    try:
        files = {"file": ("debug_test.txt", test_content, "text/plain")}
        response = requests.post(
            f"{API_BASE_URL}/notes/{note_id}/attachments",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            attachment = response.json()
            print(f"✅ File uploaded successfully: {attachment['id']}")
            print(f"   Original filename: {attachment['original_filename']}")
            print(f"   File size: {attachment['file_size']} bytes")
            print(f"   File type: {attachment['file_type']}")
            print(f"   URL: {attachment['url']}")
            return attachment['id']
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return None

def test_file_access(attachment_id):
    """Test file access via download endpoint"""
    print(f"\n⬇️ Testing file download for attachment {attachment_id}...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/attachments/{attachment_id}/download", timeout=10)
        
        if response.status_code == 200:
            print(f"✅ File download successful: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ File download failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ File download error: {e}")
        return False

def main():
    print("🐛 Media Attachment Debug Script")
    print("=" * 40)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code != 200:
            print("❌ API is not responding correctly. Please check if the application is running.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Please make sure the application is running with: docker-compose up")
        sys.exit(1)
    
    print("✅ API is running")
    
    # Run debug tests
    check_api_endpoints()
    
    note_id = test_note_creation()
    if not note_id:
        print("\n❌ Cannot proceed without a note. Check the logs above.")
        sys.exit(1)
    
    attachment_id = test_file_upload(note_id)
    if not attachment_id:
        print("\n❌ File upload failed. Check the logs above.")
        sys.exit(1)
    
    test_file_access(attachment_id)
    
    print("\n🎉 Debug tests completed!")
    print("\nIf you see any ❌ errors above, those indicate the issues to fix.")
    print("If all tests pass ✅, the media attachment functionality should be working.")

if __name__ == "__main__":
    main()
