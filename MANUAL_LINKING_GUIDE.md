# Manual Relationship Linking Guide

## Overview

The manual linking feature allows users to create relationships between notes in two ways:
1. **Interactive Graph Selection**: Click two nodes in the graph visualization to create relationships
2. **Form-Based Linking**: Use the manual linking form on the graph page

## 🎮 Interactive Graph Linking

### How to Use

1. **Navigate to Graph Page**: Go to the "Grafo de Conexões" page
2. **Switch to Link Mode**: Click the "🔗 Criar Relacionamento" button
3. **Select Source Node**: Click on the first note (origin)
4. **Select Target Node**: Click on the second note (destination)
5. **Choose Relationship**: A dialog will appear to select the relationship type
6. **Create Relationship**: Click "Criar Relacionamento" to confirm

### Visual Feedback

- **Selected nodes** are highlighted with colored borders
- **Instructions** appear when in link mode
- **Selected nodes info** shows current selection
- **Dialog preview** shows the relationship being created

### Relationship Types Available

- **RELATED**: General relationship
- **SIMILAR**: Similar content or concepts
- **PREREQUISITE**: One note is required before the other
- **FOLLOWS**: Sequential relationship
- **CONTAINS**: One note encompasses the other
- **CONTAINED_BY**: One note is part of the other
- **REFERENCES**: One note references the other
- **CONTRADICTS**: Conflicting information
- **SUPPORTS**: Supporting evidence or information
- **EXTENDS**: Builds upon or extends concepts

## 📋 Form-Based Linking

### Manual Linking Section

The graph page includes a manual linking form with:
- **Source Note Search**: Type to find the origin note
- **Target Note Search**: Type to find the destination note
- **Relationship Type**: Dropdown with available types
- **Bidirectional Option**: Create relationships in both directions

### Relationship Management

- **Load Relationships**: Select a note to view its relationships
- **Delete Relationships**: Remove existing relationships
- **Detailed View**: See relationship types and connected notes

## 🔧 API Endpoints

### Create Manual Relationship
```http
POST /notes/{note_id}/link
Content-Type: application/json

{
  "target_note_id": "target_note_id",
  "relationship_type": "RELATED",
  "bidirectional": true,
  "description": "Optional description"
}
```

### Delete Relationship
```http
DELETE /notes/{source_id}/relationships/{target_id}?bidirectional=true
```

### List Relationships
```http
GET /notes/{note_id}/relationships
```

### Get Detailed Relationships
```http
GET /notes/{note_id}/relationships/detailed
```

### Get Available Notes for Linking
```http
GET /notes/{note_id}/available-links?exclude_existing=true
```

## 💡 Best Practices

### When to Use Manual Linking

1. **Specific Relationships**: When automatic similarity isn't sufficient
2. **Domain Knowledge**: When you know relationships that aren't textually obvious
3. **Hierarchical Structure**: Creating clear prerequisite chains
4. **Cross-Domain Connections**: Linking notes from different topics

### Relationship Type Guidelines

- **PREREQUISITE/FOLLOWS**: Use for learning paths and sequential content
- **CONTAINS/CONTAINED_BY**: Use for hierarchical organization
- **SIMILAR**: Use when content is related but not automatically detected
- **REFERENCES**: Use when one note cites or mentions another
- **CONTRADICTS**: Use to highlight conflicting viewpoints
- **SUPPORTS**: Use for evidence and supporting arguments

### Graph Organization Tips

1. **Start with Prerequisites**: Create learning paths first
2. **Group Related Topics**: Use SIMILAR for topic clusters
3. **Highlight Conflicts**: Use CONTRADICTS for different approaches
4. **Build Hierarchies**: Use CONTAINS for topic organization

## 🎨 User Interface Features

### Graph Interaction Modes

- **View Mode** (👁️): Default mode for exploring the graph
- **Link Mode** (🔗): Interactive relationship creation mode

### Visual Elements

- **Mode Buttons**: Switch between view and link modes
- **Instructions Panel**: Shows how to use link mode
- **Selection Display**: Shows currently selected nodes
- **Relationship Dialog**: Modal for choosing relationship type

### Search and Discovery

- **Autocomplete Search**: Type-ahead search for note selection
- **Available Notes**: Shows notes that can be linked
- **Exclude Existing**: Option to hide already-linked notes

## 🔍 Testing

### Manual Testing Steps

1. Create test notes with different content
2. Switch to graph page and link mode
3. Select two nodes and create relationships
4. Verify relationships appear in graph
5. Test different relationship types
6. Test relationship deletion

### Automated Testing

Run the test script:
```bash
python test_manual_linking.py
```

This tests:
- Relationship creation
- Bidirectional relationships
- Relationship listing
- Available notes discovery
- Relationship deletion
- Error handling

## 🚀 Advanced Features

### Bidirectional Relationships

- **Automatic**: Creates relationships in both directions
- **Manual Control**: Option to create one-way relationships
- **Consistent Deletion**: Removes both directions when deleting

### Relationship Validation

- **Self-Reference Prevention**: Can't link a note to itself
- **Duplicate Detection**: Prevents duplicate relationships
- **Note Existence**: Validates both notes exist

### Integration with Automatic Linking

- **Coexistence**: Manual and automatic relationships work together
- **Override Capability**: Manual relationships take precedence
- **Enhanced Discovery**: Manual links improve automatic suggestions

## 🎯 Use Cases

### Academic Research
- Link papers to their prerequisites
- Connect supporting and contradicting evidence
- Build knowledge hierarchies

### Project Documentation
- Link requirements to implementations
- Connect related features
- Build dependency chains

### Personal Knowledge Management
- Create learning paths
- Link related concepts
- Build topic clusters

### Content Creation
- Link drafts to references
- Connect ideas and inspirations
- Build content hierarchies

## 🔧 Troubleshooting

### Common Issues

1. **Nodes Not Selectable**: Make sure you're in link mode
2. **Dialog Not Appearing**: Ensure both nodes are selected
3. **Relationship Not Created**: Check API connectivity
4. **Graph Not Updating**: Refresh the page or reload graph

### Error Messages

- **"Nota não encontrada"**: One of the notes doesn't exist
- **"Uma nota não pode se relacionar consigo mesma"**: Trying to link note to itself
- **"Erro ao criar relacionamento"**: API or database error

### Performance Tips

- **Limit Relationships**: Too many relationships can clutter the graph
- **Use Appropriate Types**: Choose specific relationship types
- **Regular Cleanup**: Remove outdated relationships

## 🔮 Future Enhancements

### Planned Features

1. **Relationship Weights**: Strength indicators for relationships
2. **Temporal Relationships**: Time-based relationship tracking
3. **Bulk Operations**: Create multiple relationships at once
4. **Relationship Templates**: Predefined relationship patterns
5. **Visual Customization**: Different colors for relationship types

### Integration Possibilities

1. **AI Suggestions**: ML-powered relationship recommendations
2. **Import/Export**: Relationship data portability
3. **Collaboration**: Multi-user relationship creation
4. **Analytics**: Relationship usage statistics
