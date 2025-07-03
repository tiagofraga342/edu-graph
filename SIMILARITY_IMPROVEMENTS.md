# Knowledge Graph Similarity Improvements

## Overview

This document outlines the improvements made to the knowledge graph similarity system to create more accurate and meaningful relationships between notes.

## Previous System

The original system used:
- Simple cosine similarity on embeddings from `all-MiniLM-L6-v2`
- Fixed threshold of 0.55
- Single relationship type: "SIMILAR"
- Binary decision (similar/not similar)

## Enhanced System

### 1. Multi-Dimensional Similarity Analysis

The new system calculates multiple types of similarity:

#### **Semantic Similarity** (40% weight by default)
- Uses pre-computed embeddings from sentence transformers
- Captures deep semantic meaning and context
- Best for conceptually related content

#### **Keyword Similarity** (30% weight by default)
- Uses TF-IDF vectorization with n-grams (1-2)
- Identifies shared important terms and phrases
- Effective for topically related content

#### **Structural Similarity** (15% weight by default)
- Analyzes document structure (headers, lists, code blocks, etc.)
- Identifies notes with similar formatting patterns
- Useful for notes of the same type (e.g., both tutorials, both reference docs)

#### **Topic Similarity** (15% weight by default)
- Simple keyword extraction and overlap analysis
- Focuses on domain-specific terminology
- Complements semantic analysis

### 2. Multiple Relationship Types

Instead of just "SIMILAR", the system now creates:

- **HIGHLY_RELATED** (≥0.8): Very strong overall similarity
- **SEMANTICALLY_RELATED** (≥0.7): Strong semantic connection
- **TOPICALLY_RELATED** (≥0.6): Shared topics/keywords
- **STRUCTURALLY_RELATED** (≥0.6): Similar document structure
- **KEYWORD_RELATED** (≥0.6): Strong keyword overlap
- **LOOSELY_RELATED** (≥0.5): Weak but meaningful connection

### 3. Advanced Relationship Detection

#### **Hierarchical Relationships**
- **CONTAINS**: One note encompasses concepts from another
- **CONTAINED_BY**: One note is a subset of another
- Detected through concept overlap analysis

#### **Sequential Relationships**
- **PREREQUISITE**: One note should be studied before another
- **FOLLOWS**: One note logically follows another
- Detected through pattern matching for sequential indicators

#### **Conceptual Relationships**
- **CONCEPTUALLY_RELATED**: Shared key concepts
- Uses enhanced concept extraction from text

### 4. Configurable Similarity Profiles

Pre-defined configurations for different use cases:

#### **Default**
Balanced approach suitable for most content types.

#### **Semantic Focused**
Emphasizes deep semantic understanding (60% semantic weight).

#### **Keyword Focused**
Emphasizes term overlap and TF-IDF similarity (50% keyword weight).

#### **Strict**
Higher thresholds, creates fewer but higher-quality relationships.

#### **Permissive**
Lower thresholds, creates more exploratory relationships.

#### **Academic**
Optimized for research and academic content with hierarchical detection.

#### **Creative**
Optimized for creative content with emphasis on semantic connections.

## API Endpoints

### Enhanced Analysis
```
GET /notes/{note_id}/analyze?config_name=default
```
Performs comprehensive relationship analysis without creating relationships.

### Enhanced Linking
```
POST /notes/{note_id}/link-enhanced
```
Creates relationships using advanced similarity analysis with custom configuration.

### Configuration Management
```
GET /similarity/configs
```
Lists available similarity configurations and their descriptions.

## Usage Examples

### 1. Analyze Note Relationships
```python
# Get comprehensive analysis
response = requests.get(f"/notes/{note_id}/analyze?config_name=academic")
analysis = response.json()

print(f"Semantic relationships: {len(analysis['semantic'])}")
print(f"Hierarchical relationships: {len(analysis['hierarchical'])}")
print(f"Sequential relationships: {len(analysis['sequential'])}")
```

### 2. Create Enhanced Links
```python
# Use custom configuration
config = {
    "semantic_weight": 0.5,
    "keyword_weight": 0.3,
    "min_threshold": 0.6
}

response = requests.post(f"/notes/{note_id}/link-enhanced", json=config)
result = response.json()
print(f"Created {result['total_relationships']} relationships")
```

### 3. Use Predefined Configurations
```python
# Use academic configuration
config = {"config_name": "academic"}
response = requests.post(f"/notes/{note_id}/link-enhanced", json=config)
```

## Benefits

### 1. **More Accurate Relationships**
- Multiple similarity measures reduce false positives
- Different relationship types provide semantic meaning
- Configurable thresholds allow fine-tuning

### 2. **Better Knowledge Discovery**
- Hierarchical relationships show concept containment
- Sequential relationships reveal learning paths
- Conceptual relationships connect related ideas

### 3. **Flexible Configuration**
- Different profiles for different content types
- Custom weights for specific use cases
- Adjustable thresholds for precision vs. recall

### 4. **Scalable Architecture**
- Modular similarity components
- Cacheable concept extraction
- Efficient relationship limits

## Implementation Notes

### Performance Considerations
- TF-IDF calculation is done on-demand (consider caching for large datasets)
- Concept extraction uses simple regex (can be enhanced with NLP libraries)
- Relationship limits prevent over-connection

### Future Enhancements
1. **Named Entity Recognition**: Use spaCy or similar for better concept extraction
2. **Temporal Analysis**: Consider note creation/modification times
3. **User Feedback**: Learn from user interactions with relationships
4. **Graph Metrics**: Use centrality and clustering for relationship quality
5. **Domain-Specific Models**: Fine-tuned embeddings for specific domains

## Migration

The enhanced system is backward compatible:
- Existing `link_similar_notes()` function still works
- New note creation uses enhanced linking by default
- Legacy similarity endpoint remains unchanged
- Enhanced features are opt-in through new endpoints

## Configuration Examples

### For Academic Research
```python
config = {
    "semantic_weight": 0.35,
    "keyword_weight": 0.35,
    "structural_weight": 0.2,
    "topic_weight": 0.1,
    "enable_hierarchical_detection": True,
    "enable_sequential_detection": True
}
```

### For Creative Writing
```python
config = {
    "semantic_weight": 0.5,
    "keyword_weight": 0.2,
    "structural_weight": 0.1,
    "topic_weight": 0.2,
    "semantically_related_threshold": 0.6
}
```

### For Technical Documentation
```python
config = {
    "semantic_weight": 0.3,
    "keyword_weight": 0.4,
    "structural_weight": 0.2,
    "topic_weight": 0.1,
    "enable_concept_analysis": True
}
```
