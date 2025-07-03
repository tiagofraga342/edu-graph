# Note Population Scripts

This directory contains scripts to populate the edu-graph application with the 84 example notes from `example_notes.md`.

## 📁 Files

- **`populate_notes.py`** - Main script to delete all notes and populate with example notes
- **`verify_notes.py`** - Verification script to check the populated notes
- **`example_notes.md`** - Source file containing 84 computer science notes
- **`README_populate.md`** - This documentation file

## 🚀 Quick Start

### Prerequisites

1. **Application Running**: Make sure the edu-graph application is running:
   ```bash
   docker-compose up
   ```

2. **API Accessible**: Verify the API is accessible at `http://localhost:8000`

3. **Python Requests**: Install required Python package:
   ```bash
   pip install requests
   ```

### Population Process

1. **Run the population script**:
   ```bash
   python populate_notes.py
   ```

2. **Confirm deletion** when prompted:
   ```
   ⚠️  WARNING: This will delete ALL existing notes!
   Do you want to continue? (yes/no): yes
   ```

3. **Wait for completion** (takes about 1-2 minutes):
   ```
   [12:34:56] 🚀 Note Population Script
   [12:34:56] ✅ API is running
   [12:34:56] ✅ Parsed 84 notes from file
   [12:34:57] ✅ Deleted 0 notes from MongoDB
   [12:34:58] 📝 Creating 84 notes...
   [12:35:30] ✅ Progress: 84/84 notes created
   [12:35:35] ✅ Verification: 84 notes found in database
   [12:35:35] 🎉 All notes created successfully!
   ```

4. **Verify the results**:
   ```bash
   python verify_notes.py
   ```

## 📊 What Gets Created

The script creates **84 computer science notes** covering:

### 📚 Categories
- **Data Structures** (Arrays, Lists, Trees, Graphs, etc.)
- **Algorithms** (Sorting, Searching, Graph algorithms, etc.)
- **Programming Paradigms** (OOP, Functional, Concurrent, etc.)
- **Operating Systems** (Processes, Memory, File Systems, etc.)
- **Networks** (TCP/IP, HTTP, DNS, Routing, etc.)
- **Databases** (SQL, NoSQL, Transactions, etc.)
- **Software Engineering** (Agile, Git, Design Patterns, etc.)
- **Machine Learning** (Supervised, Unsupervised, Neural Networks, etc.)

### 🔗 Features
- **Rich Content**: Each note has a title and detailed description
- **Markdown Support**: Content includes Markdown formatting
- **Automatic Relationships**: The system will automatically:
  - Generate embeddings for each note
  - Calculate similarity between notes
  - Create relationships in the Neo4j graph
  - Enable path finding between related concepts

## 🔧 Script Details

### `populate_notes.py`

**What it does:**
1. ✅ Checks API health
2. 📖 Parses `example_notes.md` file
3. 🗑️ Deletes all existing notes (with confirmation)
4. 📝 Creates 84 new notes via API
5. ⏳ Waits for processing
6. ✅ Verifies creation success

**Features:**
- Progress tracking
- Error handling and retry logic
- Detailed logging with timestamps
- Failed note tracking
- Confirmation prompt for safety

### `verify_notes.py`

**What it does:**
1. 📊 Counts notes in database
2. 🏷️ Categorizes notes by topic
3. 🔍 Checks Neo4j health and relationships
4. 🎯 Tests path finding functionality
5. 📋 Shows sample notes

## 🎯 Expected Results

After successful population:

### Database State
- **MongoDB**: 84 note documents with embeddings
- **Neo4j**: 84 note nodes with similarity relationships
- **Attachments**: None (clean slate for new attachments)

### Application Features
- **Browse Notes**: View all 84 notes in the main interface
- **Search**: Full-text search across all note content
- **Graph Visualization**: Interactive graph showing note relationships
- **Path Finding**: Discover connections between any two notes
- **Similarity**: Find related notes based on content similarity

### Sample Notes Created
```
1. Array Data Structure
2. Linked List Implementation
3. Binary Search Tree
4. Graph Traversal Algorithms
5. Object-Oriented Programming
...
84. Reinforcement Learning
```

## 🐛 Troubleshooting

### Common Issues

1. **API Not Running**
   ```
   ❌ Cannot connect to API
   ```
   **Solution**: Start the application with `docker-compose up`

2. **File Not Found**
   ```
   ❌ File not found: example_notes.md
   ```
   **Solution**: Run the script from the directory containing `example_notes.md`

3. **Partial Creation**
   ```
   ⚠️ Expected 84 notes, but found 67
   ```
   **Solution**: Check API logs for errors, may need to retry

4. **Neo4j Issues**
   ```
   ❌ Neo4j Status: error
   ```
   **Solution**: Restart Neo4j container: `docker-compose restart neo4j`

### Debug Commands

```bash
# Check API health
curl http://localhost:8000/docs

# Check Neo4j health
curl http://localhost:8000/neo4j/health

# Check current note count
curl http://localhost:8000/notes | jq length

# View application logs
docker-compose logs api
```

## 🔄 Re-running the Script

The script can be run multiple times safely:
- Always prompts for confirmation before deletion
- Cleans up all existing data before creating new notes
- Verifies results after completion

## 🎉 Next Steps

After successful population:

1. **Explore the Application**:
   - Open http://localhost:3000
   - Browse the 84 notes
   - Try the search functionality

2. **Test Graph Features**:
   - Go to "Grafo de Conexões" tab
   - Visualize the knowledge graph
   - Try path finding between different topics

3. **Add Your Own Content**:
   - Create new notes
   - Upload attachments
   - Watch the graph grow with your knowledge

The populated database provides a rich foundation for exploring the full capabilities of the edu-graph knowledge management system!
