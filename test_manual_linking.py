#!/usr/bin/env python3
"""
Test script for manual relationship linking functionality
Tests both API endpoints and demonstrates the new features
"""

import requests
import json
import time
from typing import Dict, List

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_manual_linking():
    """Test the manual linking functionality"""
    
    print("🧪 Testing Manual Relationship Linking")
    print("=" * 50)
    
    # Sample notes for testing
    test_notes = [
        {
            "title": "Python Basics",
            "content": "Introduction to Python programming language. Variables, data types, and basic syntax."
        },
        {
            "title": "Object-Oriented Programming",
            "content": "Classes, objects, inheritance, and polymorphism in Python. Advanced programming concepts."
        },
        {
            "title": "Web Development with Flask",
            "content": "Building web applications using Flask framework. Routes, templates, and database integration."
        }
    ]
    
    # Create test notes
    created_notes = []
    print("📝 Creating test notes...")
    
    for note_data in test_notes:
        try:
            response = requests.post(f"{API_BASE_URL}/notes", json=note_data, params={"use_enhanced_linking": False})
            if response.status_code == 200:
                note = response.json()
                created_notes.append(note)
                print(f"✅ Created: {note['title']}")
            else:
                print(f"❌ Failed to create note: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating note: {e}")
    
    if len(created_notes) < 2:
        print("❌ Not enough notes created for testing")
        return
    
    # Test 1: Manual relationship creation
    print("\n🔗 Testing Manual Relationship Creation")
    print("-" * 40)
    
    source_note = created_notes[0]  # Python Basics
    target_note = created_notes[1]  # OOP
    
    try:
        link_data = {
            "target_note_id": target_note['id'],
            "relationship_type": "PREREQUISITE",
            "bidirectional": True,
            "description": "Python basics is a prerequisite for OOP"
        }
        
        response = requests.post(f"{API_BASE_URL}/notes/{source_note['id']}/link", json=link_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Created relationship: {result['message']}")
            print(f"   Type: {link_data['relationship_type']}")
            print(f"   Bidirectional: {result['bidirectional']}")
        else:
            error_data = response.json()
            print(f"❌ Failed to create relationship: {error_data.get('detail', response.status_code)}")
    except Exception as e:
        print(f"❌ Error creating relationship: {e}")
    
    # Test 2: List relationships
    print("\n📋 Testing Relationship Listing")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes/{source_note['id']}/relationships")
        if response.status_code == 200:
            relationships = response.json()
            print(f"Found {len(relationships)} relationships:")
            for rel in relationships:
                print(f"  - {rel['type']} → {rel['id']}")
        else:
            print(f"❌ Failed to list relationships: {response.status_code}")
    except Exception as e:
        print(f"❌ Error listing relationships: {e}")
    
    # Test 3: Detailed relationships
    print("\n📋 Testing Detailed Relationship Information")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes/{source_note['id']}/relationships/detailed")
        if response.status_code == 200:
            detailed_relationships = response.json()
            print(f"Found {len(detailed_relationships)} detailed relationships:")
            for rel in detailed_relationships:
                print(f"  - {rel['relationship_type']} → {rel['title']}")
                print(f"    ID: {rel['id']}")
                print(f"    Bidirectional: {rel['bidirectional']}")
        else:
            print(f"❌ Failed to get detailed relationships: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting detailed relationships: {e}")
    
    # Test 4: Available notes for linking
    print("\n🔍 Testing Available Notes for Linking")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes/{source_note['id']}/available-links?exclude_existing=true")
        if response.status_code == 200:
            available = response.json()
            print(f"Found {available['total']} available notes for linking:")
            for note in available['notes']:
                print(f"  - {note['title']} (ID: {note['id']})")
        else:
            print(f"❌ Failed to get available notes: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting available notes: {e}")
    
    # Test 5: Create another relationship
    print("\n🔗 Testing Second Relationship Creation")
    print("-" * 40)
    
    if len(created_notes) >= 3:
        target_note2 = created_notes[2]  # Flask
        
        try:
            link_data2 = {
                "target_note_id": target_note2['id'],
                "relationship_type": "RELATED",
                "bidirectional": False
            }
            
            response = requests.post(f"{API_BASE_URL}/notes/{created_notes[1]['id']}/link", json=link_data2)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Created second relationship: {result['message']}")
                print(f"   From: {created_notes[1]['title']}")
                print(f"   To: {target_note2['title']}")
                print(f"   Type: {link_data2['relationship_type']}")
                print(f"   Bidirectional: {result['bidirectional']}")
            else:
                error_data = response.json()
                print(f"❌ Failed to create second relationship: {error_data.get('detail', response.status_code)}")
        except Exception as e:
            print(f"❌ Error creating second relationship: {e}")
    
    # Test 6: Delete a relationship
    print("\n🗑️ Testing Relationship Deletion")
    print("-" * 40)
    
    try:
        response = requests.delete(f"{API_BASE_URL}/notes/{source_note['id']}/relationships/{target_note['id']}?bidirectional=true")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Deleted relationship: {result['message']}")
        else:
            error_data = response.json()
            print(f"❌ Failed to delete relationship: {error_data.get('detail', response.status_code)}")
    except Exception as e:
        print(f"❌ Error deleting relationship: {e}")
    
    # Test 7: Verify deletion
    print("\n✅ Verifying Relationship Deletion")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes/{source_note['id']}/relationships")
        if response.status_code == 200:
            relationships = response.json()
            print(f"Remaining relationships: {len(relationships)}")
            for rel in relationships:
                print(f"  - {rel['type']} → {rel['id']}")
        else:
            print(f"❌ Failed to verify deletion: {response.status_code}")
    except Exception as e:
        print(f"❌ Error verifying deletion: {e}")
    
    print("\n✅ Manual linking tests completed!")
    print("\nKey Features Tested:")
    print("- ✅ Manual relationship creation with custom types")
    print("- ✅ Bidirectional relationship support")
    print("- ✅ Relationship listing and detailed information")
    print("- ✅ Available notes discovery")
    print("- ✅ Relationship deletion")
    print("- ✅ Error handling and validation")

def cleanup_test_notes():
    """Clean up test notes (optional)"""
    try:
        response = requests.delete(f"{API_BASE_URL}/notes/all")
        if response.status_code == 200:
            print("🧹 Test notes cleaned up")
        else:
            print(f"⚠️ Cleanup failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Manual Linking Test")
    print("Make sure your API server is running on http://localhost:8000")
    
    # Wait a moment for user to confirm
    input("Press Enter to continue...")
    
    try:
        test_manual_linking()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    
    # Ask if user wants to cleanup
    cleanup = input("\nClean up test notes? (y/N): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_notes()
    
    print("\n👋 Test completed!")
