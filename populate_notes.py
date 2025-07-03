#!/usr/bin/env python3
"""
Script to delete all current notes and populate the database with notes from example_notes.md
"""
import requests
import re
import time
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def debug_print(message):
    """Print debug message with timestamp"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def check_api_health():
    """Check if API is running"""
    debug_print("🔍 Checking API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            debug_print("✅ API is running")
            return True
        else:
            debug_print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        debug_print(f"❌ Cannot connect to API: {e}")
        return False

def delete_all_notes():
    """Delete all existing notes"""
    debug_print("🗑️ Deleting all existing notes...")
    
    try:
        # First get all notes to see how many we're deleting
        response = requests.get(f"{API_BASE_URL}/notes", timeout=10)
        if response.status_code == 200:
            existing_notes = response.json()
            debug_print(f"📊 Found {len(existing_notes)} existing notes")
        else:
            debug_print("⚠️ Could not get existing notes count")
            existing_notes = []
        
        # Delete all notes
        response = requests.delete(f"{API_BASE_URL}/notes", timeout=30)
        if response.status_code == 200:
            result = response.json()
            debug_print(f"✅ Deleted {result.get('deleted_mongo', 0)} notes from MongoDB")
            debug_print(f"✅ Deleted {result.get('deleted_neo4j', 'all')} nodes from Neo4j")
            return True
        else:
            debug_print(f"❌ Failed to delete notes: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        debug_print(f"❌ Error deleting notes: {e}")
        return False

def parse_notes_file(file_path):
    """Parse the example_notes.md file and extract notes"""
    debug_print(f"📖 Parsing notes from {file_path}...")
    
    if not Path(file_path).exists():
        debug_print(f"❌ File not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        notes = []
        # Split by double newlines to get each note block
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 2:
                # First line should be the title (number. **Title**)
                title_line = lines[0].strip()
                # Remaining lines are the content
                content_lines = lines[1:]
                
                # Extract title using regex
                title_match = re.match(r'^\d+\.\s*\*\*(.*?)\*\*\s*$', title_line)
                if title_match:
                    title = title_match.group(1).strip()
                    content = '\n'.join(content_lines).strip()
                    
                    if title and content:
                        notes.append({
                            'title': title,
                            'content': content
                        })
        
        debug_print(f"✅ Parsed {len(notes)} notes from file")
        return notes
        
    except Exception as e:
        debug_print(f"❌ Error parsing file: {e}")
        return []

def create_note(title, content):
    """Create a single note via API"""
    try:
        data = {
            'title': title,
            'content': content
        }
        
        response = requests.post(f"{API_BASE_URL}/notes", json=data, timeout=15)
        if response.status_code == 200:
            note = response.json()
            return note
        else:
            debug_print(f"❌ Failed to create note '{title}': {response.status_code}")
            return None
            
    except Exception as e:
        debug_print(f"❌ Error creating note '{title}': {e}")
        return None

def populate_notes(notes):
    """Create all notes in the database"""
    debug_print(f"📝 Creating {len(notes)} notes...")

    created_count = 0
    failed_count = 0
    failed_notes = []

    for i, note_data in enumerate(notes, 1):
        title = note_data['title']
        content = note_data['content']

        # Show progress for every note, but less verbose for large batches
        if len(notes) <= 20 or i % 5 == 0 or i == 1:
            debug_print(f"Creating note {i}/{len(notes)}: {title}")

        note = create_note(title, content)
        if note:
            created_count += 1
            if i % 10 == 0:  # Progress update every 10 notes
                debug_print(f"✅ Progress: {i}/{len(notes)} notes created")
        else:
            failed_count += 1
            failed_notes.append(title)

        # Small delay to avoid overwhelming the API
        time.sleep(0.1)

    debug_print(f"📊 Summary: {created_count} created, {failed_count} failed")

    if failed_notes:
        debug_print("❌ Failed notes:")
        for title in failed_notes[:5]:  # Show first 5 failed notes
            debug_print(f"   - {title}")
        if len(failed_notes) > 5:
            debug_print(f"   ... and {len(failed_notes) - 5} more")

    return created_count, failed_count

def wait_for_processing():
    """Wait for similarity processing to complete"""
    debug_print("⏳ Waiting for similarity processing...")
    time.sleep(5)  # Give time for embeddings and similarity calculations

def verify_notes():
    """Verify that notes were created successfully"""
    debug_print("🔍 Verifying created notes...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/notes", timeout=15)
        if response.status_code == 200:
            notes = response.json()
            debug_print(f"✅ Verification: {len(notes)} notes found in database")
            
            # Show sample of created notes
            if notes:
                debug_print("📋 Sample of created notes:")
                for note in notes[:5]:
                    debug_print(f"   - {note['title']}")
                if len(notes) > 5:
                    debug_print(f"   ... and {len(notes) - 5} more")
            
            return len(notes)
        else:
            debug_print(f"❌ Failed to verify notes: {response.status_code}")
            return 0
            
    except Exception as e:
        debug_print(f"❌ Error verifying notes: {e}")
        return 0

def main():
    debug_print("🚀 Note Population Script")
    debug_print("=" * 50)
    
    # Check API health
    if not check_api_health():
        debug_print("❌ API is not available. Please start the application first.")
        debug_print("Run: docker-compose up")
        sys.exit(1)
    
    # Parse notes from file
    notes = parse_notes_file("example_notes.md")
    if not notes:
        debug_print("❌ No notes found in example_notes.md")
        sys.exit(1)
    
    debug_print(f"📊 Found {len(notes)} notes to create")
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will delete ALL existing notes!")
    confirm = input("Do you want to continue? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        debug_print("❌ Operation cancelled by user")
        sys.exit(0)
    
    # Delete existing notes
    if not delete_all_notes():
        debug_print("❌ Failed to delete existing notes")
        sys.exit(1)
    
    # Wait a moment for deletion to complete
    time.sleep(2)
    
    # Create new notes
    created_count, failed_count = populate_notes(notes)
    
    if failed_count > 0:
        debug_print(f"⚠️ {failed_count} notes failed to create")
    
    if created_count == 0:
        debug_print("❌ No notes were created successfully")
        sys.exit(1)
    
    # Wait for processing
    wait_for_processing()
    
    # Verify results
    final_count = verify_notes()
    
    if final_count == len(notes):
        debug_print("🎉 All notes created successfully!")
        debug_print(f"✅ Database now contains {final_count} notes")
    else:
        debug_print(f"⚠️ Expected {len(notes)} notes, but found {final_count}")
    
    debug_print("\n🔗 You can now:")
    debug_print("   - View notes at: http://localhost:3000")
    debug_print("   - Explore the graph at: http://localhost:3000 (Graph tab)")
    debug_print("   - Test path finding between notes")

if __name__ == "__main__":
    main()
