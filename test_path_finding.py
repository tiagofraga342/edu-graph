#!/usr/bin/env python3
"""
Test script for path finding functionality
"""
import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def debug_print(message):
    """Print debug message with timestamp"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_test_notes():
    """Create a set of test notes for path finding"""
    debug_print("📝 Creating test notes...")
    
    test_notes = [
        {"title": "Machine Learning Basics", "content": "Introduction to ML concepts and algorithms"},
        {"title": "Neural Networks", "content": "Deep learning and neural network architectures"},
        {"title": "Data Science", "content": "Data analysis, statistics, and visualization"},
        {"title": "Python Programming", "content": "Python syntax, libraries, and best practices"},
        {"title": "Statistics", "content": "Statistical methods and probability theory"},
        {"title": "Linear Algebra", "content": "Vectors, matrices, and mathematical foundations"}
    ]
    
    created_notes = []
    for note_data in test_notes:
        try:
            response = requests.post(f"{API_BASE_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                note = response.json()
                created_notes.append(note)
                debug_print(f"✅ Created note: {note['title']} (ID: {note['id']})")
            else:
                debug_print(f"❌ Failed to create note: {note_data['title']}")
        except Exception as e:
            debug_print(f"❌ Error creating note {note_data['title']}: {e}")
    
    return created_notes

def create_test_relationships(notes):
    """Create relationships between test notes"""
    debug_print("🔗 Creating test relationships...")
    
    if len(notes) < 6:
        debug_print("❌ Not enough notes to create relationships")
        return False
    
    # Create a connected graph structure
    relationships = [
        (0, 1),  # ML Basics -> Neural Networks
        (0, 2),  # ML Basics -> Data Science
        (1, 3),  # Neural Networks -> Python
        (2, 3),  # Data Science -> Python
        (2, 4),  # Data Science -> Statistics
        (4, 5),  # Statistics -> Linear Algebra
        (3, 5),  # Python -> Linear Algebra
    ]
    
    success_count = 0
    for from_idx, to_idx in relationships:
        try:
            from_id = notes[from_idx]['id']
            to_id = notes[to_idx]['id']
            
            # Create relationship via similarity endpoint (this will create Neo4j relationships)
            response = requests.get(f"{API_BASE_URL}/notes/{from_id}/similar", timeout=10)
            if response.status_code == 200:
                success_count += 1
                debug_print(f"✅ Created relationship: {notes[from_idx]['title']} -> {notes[to_idx]['title']}")
            
        except Exception as e:
            debug_print(f"❌ Error creating relationship: {e}")
    
    debug_print(f"✅ Created {success_count} relationships")
    return success_count > 0

def test_shortest_path(notes):
    """Test shortest path finding"""
    debug_print("🎯 Testing shortest path finding...")
    
    if len(notes) < 2:
        debug_print("❌ Not enough notes for path testing")
        return False
    
    start_note = notes[0]  # ML Basics
    end_note = notes[-1]   # Linear Algebra
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/notes/{start_note['id']}/path-to/{end_note['id']}?max_depth=6",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('path'):
                path = result['path']
                debug_print(f"✅ Found shortest path with {path['length']} steps:")
                debug_print(f"   Path: {' -> '.join(path['node_ids'])}")
                debug_print(f"   Relationships: {' -> '.join(path['relationship_types'])}")
                return True
            else:
                debug_print(f"❌ No path found: {result.get('error', 'Unknown error')}")
                return False
        else:
            debug_print(f"❌ API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        debug_print(f"❌ Error testing shortest path: {e}")
        return False

def test_all_paths(notes):
    """Test finding all paths"""
    debug_print("🔀 Testing all paths finding...")
    
    if len(notes) < 2:
        debug_print("❌ Not enough notes for path testing")
        return False
    
    start_note = notes[0]  # ML Basics
    end_note = notes[3]    # Python Programming
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/notes/{start_note['id']}/all-paths-to/{end_note['id']}?max_depth=4&max_paths=5",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('paths'):
                debug_print(f"✅ Found {result['count']} path(s):")
                for i, path in enumerate(result['paths']):
                    debug_print(f"   Path {i+1}: {path['length']} steps - {' -> '.join(path['node_ids'])}")
                return True
            else:
                debug_print(f"❌ No paths found: {result.get('error', 'Unknown error')}")
                return False
        else:
            debug_print(f"❌ API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        debug_print(f"❌ Error testing all paths: {e}")
        return False

def test_neighbors(notes):
    """Test neighbor finding"""
    debug_print("👥 Testing neighbor finding...")
    
    if len(notes) < 1:
        debug_print("❌ No notes for neighbor testing")
        return False
    
    test_note = notes[0]  # ML Basics
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/notes/{test_note['id']}/neighbors?depth=2",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            debug_print(f"✅ Found {result['count']} neighbor(s):")
            for neighbor in result['neighbors']:
                debug_print(f"   Distance {neighbor['distance']}: {neighbor['id']}")
            return True
        else:
            debug_print(f"❌ API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        debug_print(f"❌ Error testing neighbors: {e}")
        return False

def cleanup_test_notes(notes):
    """Clean up test notes"""
    debug_print("🧹 Cleaning up test notes...")
    
    for note in notes:
        try:
            response = requests.delete(f"{API_BASE_URL}/notes/{note['id']}", timeout=10)
            if response.status_code == 200:
                debug_print(f"✅ Deleted note: {note['title']}")
            else:
                debug_print(f"❌ Failed to delete note: {note['title']}")
        except Exception as e:
            debug_print(f"❌ Error deleting note {note['title']}: {e}")

def main():
    debug_print("🧪 Testing Path Finding Functionality")
    debug_print("=" * 50)
    
    # Check API health
    if not check_api_health():
        debug_print("❌ API is not running. Please start the application first.")
        return
    
    debug_print("✅ API is running")
    
    # Create test data
    notes = create_test_notes()
    if not notes:
        debug_print("❌ Failed to create test notes")
        return
    
    # Wait a moment for similarity processing
    debug_print("⏳ Waiting for similarity processing...")
    time.sleep(3)
    
    # Create relationships
    if not create_test_relationships(notes):
        debug_print("❌ Failed to create relationships")
        cleanup_test_notes(notes)
        return
    
    # Wait for Neo4j processing
    debug_print("⏳ Waiting for Neo4j processing...")
    time.sleep(2)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_shortest_path(notes):
        tests_passed += 1
    
    if test_all_paths(notes):
        tests_passed += 1
    
    if test_neighbors(notes):
        tests_passed += 1
    
    # Clean up
    cleanup_test_notes(notes)
    
    # Results
    debug_print(f"\n🎉 Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        debug_print("✅ All path finding tests passed!")
    else:
        debug_print("❌ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
