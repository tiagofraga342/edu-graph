#!/usr/bin/env python3
"""
Script to verify the notes were populated correctly
"""
import requests
import time

API_BASE_URL = "http://localhost:8000"

def debug_print(message):
    """Print debug message with timestamp"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def check_notes_count():
    """Check how many notes are in the database"""
    debug_print("🔍 Checking notes count...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes", timeout=10)
        if response.status_code == 200:
            notes = response.json()
            debug_print(f"📊 Found {len(notes)} notes in database")
            return notes
        else:
            debug_print(f"❌ Failed to get notes: {response.status_code}")
            return []
    except Exception as e:
        debug_print(f"❌ Error getting notes: {e}")
        return []

def check_neo4j_health():
    """Check Neo4j status"""
    debug_print("🔍 Checking Neo4j health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/neo4j/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            debug_print(f"✅ Neo4j Status: {health['status']}")
            debug_print(f"📊 Note nodes in Neo4j: {health.get('note_nodes', 0)}")
            debug_print(f"📊 Total relationships: {health.get('total_relationships', 0)}")
            return health
        else:
            debug_print(f"❌ Neo4j health check failed: {response.status_code}")
            return None
    except Exception as e:
        debug_print(f"❌ Error checking Neo4j: {e}")
        return None

def test_sample_path_finding(notes):
    """Test path finding with a few sample notes"""
    if len(notes) < 2:
        debug_print("⚠️ Not enough notes for path finding test")
        return
    
    debug_print("🔍 Testing path finding...")
    
    # Test with first and last notes
    start_note = notes[0]
    end_note = notes[-1]
    
    try:
        url = f"{API_BASE_URL}/notes/{start_note['id']}/path-to/{end_note['id']}?max_depth=6"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('path'):
                path = result['path']
                debug_print(f"✅ Path found: {path['length']} steps")
                debug_print(f"   From: {start_note['title']}")
                debug_print(f"   To: {end_note['title']}")
            else:
                debug_print(f"⚠️ No path found: {result.get('error', 'Unknown reason')}")
        else:
            debug_print(f"❌ Path finding failed: {response.status_code}")
            
    except Exception as e:
        debug_print(f"❌ Error testing path finding: {e}")

def show_sample_notes(notes, count=10):
    """Show a sample of notes"""
    debug_print(f"📋 Sample of notes (showing {min(count, len(notes))}):")
    
    for i, note in enumerate(notes[:count]):
        debug_print(f"   {i+1}. {note['title']}")
        if note.get('attachments'):
            debug_print(f"      📎 {len(note['attachments'])} attachment(s)")
    
    if len(notes) > count:
        debug_print(f"   ... and {len(notes) - count} more notes")

def check_categories(notes):
    """Analyze note categories based on titles"""
    debug_print("🏷️ Analyzing note categories...")
    
    categories = {
        'Data Structures': 0,
        'Algorithms': 0,
        'Programming': 0,
        'Operating Systems': 0,
        'Networks': 0,
        'Databases': 0,
        'Software Engineering': 0,
        'Machine Learning': 0,
        'Other': 0
    }
    
    # Simple keyword-based categorization
    for note in notes:
        title = note['title'].lower()
        content = note['content'].lower()
        
        if any(word in title for word in ['array', 'list', 'stack', 'queue', 'tree', 'heap', 'hash', 'graph', 'trie', 'set']):
            categories['Data Structures'] += 1
        elif any(word in title for word in ['sort', 'search', 'algorithm', 'dijkstra', 'bellman', 'floyd', 'prim', 'kruskal', 'dfs', 'bfs']):
            categories['Algorithms'] += 1
        elif any(word in title for word in ['programming', 'oop', 'functional', 'procedural', 'logic', 'concurrent']):
            categories['Programming'] += 1
        elif any(word in title for word in ['process', 'thread', 'cpu', 'memory', 'file system', 'deadlock', 'ipc', 'os']):
            categories['Operating Systems'] += 1
        elif any(word in title for word in ['network', 'tcp', 'http', 'dns', 'dhcp', 'routing', 'switching', 'osi']):
            categories['Networks'] += 1
        elif any(word in title for word in ['database', 'sql', 'nosql', 'transaction', 'acid', 'indexing', 'sharding']):
            categories['Databases'] += 1
        elif any(word in title for word in ['agile', 'scrum', 'git', 'design pattern', 'tdd', 'ci', 'cd', 'uml']):
            categories['Software Engineering'] += 1
        elif any(word in title for word in ['learning', 'neural', 'supervised', 'unsupervised', 'reinforcement']):
            categories['Machine Learning'] += 1
        else:
            categories['Other'] += 1
    
    debug_print("📊 Note categories:")
    for category, count in categories.items():
        if count > 0:
            debug_print(f"   {category}: {count} notes")

def main():
    debug_print("🔍 Note Verification Script")
    debug_print("=" * 40)
    
    # Check notes
    notes = check_notes_count()
    if not notes:
        debug_print("❌ No notes found in database")
        return
    
    # Show sample notes
    show_sample_notes(notes)
    
    # Analyze categories
    check_categories(notes)
    
    # Check Neo4j
    neo4j_health = check_neo4j_health()
    
    # Test path finding if Neo4j is healthy
    if neo4j_health and neo4j_health.get('status') == 'healthy':
        test_sample_path_finding(notes)
    
    # Summary
    debug_print("\n📊 Verification Summary:")
    debug_print(f"   Total notes: {len(notes)}")
    debug_print(f"   Expected: 84 notes")
    
    if len(notes) == 84:
        debug_print("✅ Perfect! All 84 notes are present")
    elif len(notes) > 80:
        debug_print("✅ Good! Most notes are present")
    else:
        debug_print("⚠️ Some notes may be missing")
    
    debug_print("\n🌐 Access the application:")
    debug_print("   - Notes: http://localhost:3000")
    debug_print("   - Graph: http://localhost:3000 (click 'Grafo de Conexões')")

if __name__ == "__main__":
    main()
