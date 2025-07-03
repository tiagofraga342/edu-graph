#!/usr/bin/env python3
"""
Quick debug script to test the path finding issue
"""
import requests
import time

API_BASE_URL = "http://localhost:8000"

def debug_print(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def test_neo4j_health():
    """Test Neo4j health endpoint"""
    debug_print("🔍 Testing Neo4j health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/neo4j/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            debug_print(f"✅ Neo4j Health: {health}")
            return health
        else:
            debug_print(f"❌ Neo4j health check failed: {response.status_code}")
            debug_print(f"Response: {response.text}")
            return None
    except Exception as e:
        debug_print(f"❌ Error checking Neo4j health: {e}")
        return None

def get_sample_notes():
    """Get some sample notes for testing"""
    debug_print("🔍 Getting sample notes...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes", timeout=10)
        if response.status_code == 200:
            notes = response.json()
            debug_print(f"✅ Got {len(notes)} notes")
            return notes[:2] if len(notes) >= 2 else notes
        else:
            debug_print(f"❌ Failed to get notes: {response.status_code}")
            return []
    except Exception as e:
        debug_print(f"❌ Error getting notes: {e}")
        return []

def test_path_finding(start_id, end_id):
    """Test path finding with detailed error reporting"""
    debug_print(f"🔍 Testing path finding: {start_id} -> {end_id}")
    
    try:
        url = f"{API_BASE_URL}/notes/{start_id}/path-to/{end_id}?max_depth=6"
        debug_print(f"🔧 URL: {url}")
        
        response = requests.get(url, timeout=30)
        debug_print(f"🔧 Response status: {response.status_code}")
        debug_print(f"🔧 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            debug_print(f"✅ Success: {result}")
            return True
        else:
            debug_print(f"❌ Error response: {response.text}")
            return False
            
    except Exception as e:
        debug_print(f"❌ Exception during path finding: {e}")
        return False

def create_simple_test_notes():
    """Create two simple test notes"""
    debug_print("📝 Creating simple test notes...")
    
    notes_data = [
        {"title": "Test Note A", "content": "This is test note A for path finding"},
        {"title": "Test Note B", "content": "This is test note B for path finding"}
    ]
    
    created_notes = []
    for note_data in notes_data:
        try:
            response = requests.post(f"{API_BASE_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                note = response.json()
                created_notes.append(note)
                debug_print(f"✅ Created: {note['title']} (ID: {note['id']})")
            else:
                debug_print(f"❌ Failed to create note: {response.status_code}")
        except Exception as e:
            debug_print(f"❌ Error creating note: {e}")
    
    return created_notes

def main():
    debug_print("🐛 Quick Debug for Path Finding")
    debug_print("=" * 40)
    
    # Test API connection
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        if response.status_code != 200:
            debug_print("❌ API not responding")
            return
    except:
        debug_print("❌ Cannot connect to API")
        return
    
    debug_print("✅ API is running")
    
    # Test Neo4j health
    health = test_neo4j_health()
    if not health or health.get("status") != "healthy":
        debug_print("❌ Neo4j is not healthy")
        return
    
    # Get existing notes or create test notes
    notes = get_sample_notes()
    if len(notes) < 2:
        debug_print("⚠️ Not enough notes, creating test notes...")
        notes = create_simple_test_notes()
        
        if len(notes) < 2:
            debug_print("❌ Could not create test notes")
            return
        
        # Wait a moment for processing
        debug_print("⏳ Waiting for note processing...")
        time.sleep(3)
    
    # Test path finding
    start_id = notes[0]['id']
    end_id = notes[1]['id']
    
    debug_print(f"🎯 Testing with notes:")
    debug_print(f"   Start: {notes[0]['title']} ({start_id})")
    debug_print(f"   End: {notes[1]['title']} ({end_id})")
    
    success = test_path_finding(start_id, end_id)
    
    if success:
        debug_print("🎉 Path finding test passed!")
    else:
        debug_print("❌ Path finding test failed!")
        debug_print("💡 Check the API logs for detailed error information")

if __name__ == "__main__":
    main()
