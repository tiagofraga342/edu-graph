#!/usr/bin/env python3
"""
Debug script to check Neo4j connection and data
"""
import requests
import time
from neo4j import GraphDatabase

API_BASE_URL = "http://localhost:8000"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

def debug_print(message):
    """Print debug message with timestamp"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def test_neo4j_connection():
    """Test direct Neo4j connection"""
    debug_print("🔍 Testing Neo4j connection...")
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                debug_print("✅ Neo4j connection successful")
                return driver
            else:
                debug_print("❌ Neo4j connection failed - no response")
                return None
                
    except Exception as e:
        debug_print(f"❌ Neo4j connection error: {e}")
        return None

def check_neo4j_nodes(driver):
    """Check what nodes exist in Neo4j"""
    debug_print("🔍 Checking Neo4j nodes...")
    
    try:
        with driver.session() as session:
            # Count all nodes
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            record = result.single()
            total_nodes = record["total_nodes"] if record else 0
            debug_print(f"📊 Total nodes in Neo4j: {total_nodes}")
            
            # Count Note nodes specifically
            result = session.run("MATCH (n:Note) RETURN count(n) as note_nodes")
            record = result.single()
            note_nodes = record["note_nodes"] if record else 0
            debug_print(f"📊 Note nodes in Neo4j: {note_nodes}")
            
            # List some Note nodes
            if note_nodes > 0:
                result = session.run("MATCH (n:Note) RETURN n.id as id LIMIT 10")
                debug_print("📋 Sample Note IDs in Neo4j:")
                for record in result:
                    debug_print(f"   - {record['id']}")
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total_rels")
            record = result.single()
            total_rels = record["total_rels"] if record else 0
            debug_print(f"📊 Total relationships in Neo4j: {total_rels}")
            
            return note_nodes > 0
            
    except Exception as e:
        debug_print(f"❌ Error checking Neo4j nodes: {e}")
        return False

def get_notes_from_api():
    """Get notes from the API"""
    debug_print("🔍 Getting notes from API...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes", timeout=10)
        if response.status_code == 200:
            notes = response.json()
            debug_print(f"📊 Notes from API: {len(notes)}")
            return notes
        else:
            debug_print(f"❌ API error: {response.status_code}")
            return []
    except Exception as e:
        debug_print(f"❌ Error getting notes from API: {e}")
        return []

def test_specific_path(driver, start_id, end_id):
    """Test path finding for specific note IDs"""
    debug_print(f"🔍 Testing path between {start_id} and {end_id}...")
    
    try:
        with driver.session() as session:
            # Check if both nodes exist
            check_query = """
            MATCH (start:Note {id: $start_id})
            MATCH (end:Note {id: $end_id})
            RETURN start.id as start_exists, end.id as end_exists
            """
            
            result = session.run(check_query, start_id=start_id, end_id=end_id)
            record = result.single()
            
            if not record:
                debug_print("❌ One or both nodes not found in Neo4j")
                return False
            
            debug_print("✅ Both nodes exist in Neo4j")
            
            # Try to find any path
            path_query = """
            MATCH (start:Note {id: $start_id}), (end:Note {id: $end_id})
            MATCH path = shortestPath((start)-[*1..6]-(end))
            RETURN path, length(path) as path_length
            """
            
            result = session.run(path_query, start_id=start_id, end_id=end_id)
            record = result.single()
            
            if record and record["path"]:
                debug_print(f"✅ Path found with length: {record['path_length']}")
                return True
            else:
                debug_print("❌ No path found between nodes")
                return False
                
    except Exception as e:
        debug_print(f"❌ Error testing specific path: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_test_relationships(driver, notes):
    """Create some test relationships if none exist"""
    debug_print("🔧 Creating test relationships...")
    
    if len(notes) < 2:
        debug_print("❌ Not enough notes to create relationships")
        return False
    
    try:
        with driver.session() as session:
            # Create a simple relationship between first two notes
            note1_id = notes[0]['id']
            note2_id = notes[1]['id']
            
            # First ensure both nodes exist
            session.run("MERGE (n:Note {id: $id})", id=note1_id)
            session.run("MERGE (n:Note {id: $id})", id=note2_id)
            
            # Create relationship
            session.run("""
                MATCH (a:Note {id: $from_id}), (b:Note {id: $to_id})
                MERGE (a)-[r:RELATED]->(b)
            """, from_id=note1_id, to_id=note2_id)
            
            debug_print(f"✅ Created relationship: {note1_id} -> {note2_id}")
            return True
            
    except Exception as e:
        debug_print(f"❌ Error creating test relationships: {e}")
        return False

def main():
    debug_print("🐛 Neo4j Debug Script")
    debug_print("=" * 40)
    
    # Test Neo4j connection
    driver = test_neo4j_connection()
    if not driver:
        debug_print("❌ Cannot connect to Neo4j. Check if Neo4j is running.")
        return
    
    # Check existing data
    has_notes = check_neo4j_nodes(driver)
    
    # Get notes from API
    notes = get_notes_from_api()
    if not notes:
        debug_print("❌ No notes available from API")
        driver.close()
        return
    
    # If no notes in Neo4j, create some
    if not has_notes:
        debug_print("⚠️ No Note nodes found in Neo4j, creating them...")
        try:
            with driver.session() as session:
                for note in notes[:5]:  # Create first 5 notes
                    session.run("MERGE (n:Note {id: $id})", id=note['id'])
                    debug_print(f"✅ Created Note node: {note['id']}")
        except Exception as e:
            debug_print(f"❌ Error creating Note nodes: {e}")
    
    # Create test relationships
    create_test_relationships(driver, notes)
    
    # Test path finding with first two notes
    if len(notes) >= 2:
        test_specific_path(driver, notes[0]['id'], notes[1]['id'])
    
    # Test API endpoint
    if len(notes) >= 2:
        debug_print("🔍 Testing API endpoint...")
        try:
            response = requests.get(
                f"{API_BASE_URL}/notes/{notes[0]['id']}/path-to/{notes[1]['id']}?max_depth=6",
                timeout=10
            )
            debug_print(f"API response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                debug_print(f"API response: {result}")
            else:
                debug_print(f"API error response: {response.text}")
        except Exception as e:
            debug_print(f"❌ Error testing API endpoint: {e}")
    
    driver.close()
    debug_print("🎉 Debug completed!")

if __name__ == "__main__":
    main()
