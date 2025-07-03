# advanced_similarity.py
"""
Advanced similarity analysis for knowledge graph construction
Includes temporal, contextual, and hierarchical relationship detection
"""

from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter
from db.mongo import get_all_notes, get_note
from db.neo4j import create_relationship, get_relationships
from services.similarity import calculate_comprehensive_similarity
import logging

logger = logging.getLogger(__name__)

class AdvancedSimilarityAnalyzer:
    """Advanced similarity analyzer for knowledge graphs"""
    
    def __init__(self):
        self.concept_cache = {}
        self.relationship_history = defaultdict(list)
    
    def extract_concepts(self, text: str) -> Set[str]:
        """Extract key concepts from text using simple NLP techniques"""
        # This is a simplified version - you could use spaCy or NLTK for better results
        
        # Extract potential concepts (capitalized words, technical terms)
        concepts = set()
        
        # Capitalized words (potential proper nouns/concepts)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        concepts.update(capitalized)
        
        # Technical terms (words with numbers, underscores, or specific patterns)
        technical = re.findall(r'\b[a-zA-Z]+(?:_[a-zA-Z]+)*\b', text)
        concepts.update([t for t in technical if '_' in t])
        
        # Words in code blocks or backticks
        code_terms = re.findall(r'`([^`]+)`', text)
        concepts.update(code_terms)
        
        # Filter out common words and short terms
        filtered_concepts = {
            concept.lower() for concept in concepts 
            if len(concept) > 2 and concept.lower() not in {
                'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had'
            }
        }
        
        return filtered_concepts
    
    def calculate_concept_overlap(self, text1: str, text2: str) -> float:
        """Calculate similarity based on shared concepts"""
        concepts1 = self.extract_concepts(text1)
        concepts2 = self.extract_concepts(text2)
        
        if not concepts1 and not concepts2:
            return 0.0
        if not concepts1 or not concepts2:
            return 0.0
        
        intersection = len(concepts1.intersection(concepts2))
        union = len(concepts1.union(concepts2))
        
        return intersection / union if union > 0 else 0.0
    
    def detect_hierarchical_relationship(self, text1: str, text2: str) -> Optional[str]:
        """
        Detect if one note is a subset/superset of another
        Returns: 'CONTAINS', 'CONTAINED_BY', or None
        """
        concepts1 = self.extract_concepts(text1)
        concepts2 = self.extract_concepts(text2)
        
        if not concepts1 or not concepts2:
            return None
        
        overlap = concepts1.intersection(concepts2)
        
        # If one note's concepts are largely contained in another
        if len(overlap) / len(concepts1) > 0.8 and len(concepts1) < len(concepts2):
            return 'CONTAINED_BY'  # text1 is contained by text2
        elif len(overlap) / len(concepts2) > 0.8 and len(concepts2) < len(concepts1):
            return 'CONTAINS'  # text1 contains text2
        
        return None
    
    def detect_sequential_relationship(self, note1: Dict, note2: Dict) -> Optional[str]:
        """
        Detect if notes have a sequential relationship (prerequisite, follows, etc.)
        """
        text1 = note1.get('content', '')
        text2 = note2.get('content', '')
        
        # Look for sequential indicators
        sequential_patterns = {
            'PREREQUISITE': [
                r'\b(?:before|prerequisite|required|foundation|basic|intro)\b',
                r'\b(?:first|start|begin|initial)\b'
            ],
            'FOLLOWS': [
                r'\b(?:after|following|next|advanced|continue)\b',
                r'\b(?:then|subsequently|later)\b'
            ]
        }
        
        for rel_type, patterns in sequential_patterns.items():
            score1 = sum(len(re.findall(pattern, text1, re.IGNORECASE)) for pattern in patterns)
            score2 = sum(len(re.findall(pattern, text2, re.IGNORECASE)) for pattern in patterns)
            
            if score1 > score2 and score1 > 2:
                return rel_type
        
        return None
    
    def analyze_note_relationships(
        self, 
        note_id: str, 
        embedding: List[float],
        advanced_analysis: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Comprehensive relationship analysis for a note
        
        Returns:
            Dictionary with different types of relationships found
        """
        note = get_note(note_id)
        if not note:
            return {}
        
        note_content = note.get('content', '')
        existing_notes = get_all_notes()
        
        relationships = {
            'semantic': [],
            'hierarchical': [],
            'sequential': [],
            'conceptual': [],
            'weak': []
        }
        
        for other_note in existing_notes:
            if other_note['id'] == note_id:
                continue
            
            other_content = other_note.get('content', '')
            other_embedding = other_note.get('embedding', [])
            
            if not other_embedding:
                continue
            
            try:
                # Basic comprehensive similarity
                similarities = calculate_comprehensive_similarity(
                    note_content, other_content, embedding, other_embedding
                )
                
                # Determine relationship category
                if similarities['overall'] >= 0.7:
                    relationships['semantic'].append({
                        'note_id': other_note['id'],
                        'score': similarities['overall'],
                        'type': 'SEMANTICALLY_RELATED',
                        'details': similarities
                    })
                
                if advanced_analysis:
                    # Hierarchical analysis
                    hierarchical = self.detect_hierarchical_relationship(note_content, other_content)
                    if hierarchical:
                        relationships['hierarchical'].append({
                            'note_id': other_note['id'],
                            'type': hierarchical,
                            'score': similarities['overall']
                        })
                    
                    # Sequential analysis
                    sequential = self.detect_sequential_relationship(note, other_note)
                    if sequential:
                        relationships['sequential'].append({
                            'note_id': other_note['id'],
                            'type': sequential,
                            'score': similarities['overall']
                        })
                    
                    # Conceptual overlap
                    concept_score = self.calculate_concept_overlap(note_content, other_content)
                    if concept_score >= 0.3:
                        relationships['conceptual'].append({
                            'note_id': other_note['id'],
                            'score': concept_score,
                            'type': 'CONCEPTUALLY_RELATED'
                        })
                
                # Weak relationships (might be useful for exploration)
                elif similarities['overall'] >= 0.4:
                    relationships['weak'].append({
                        'note_id': other_note['id'],
                        'score': similarities['overall'],
                        'type': 'WEAKLY_RELATED',
                        'details': similarities
                    })
                    
            except Exception as e:
                logger.error(f"Error analyzing relationship with note {other_note['id']}: {e}")
                continue
        
        return relationships
    
    def create_smart_relationships(
        self, 
        note_id: str, 
        embedding: List[float],
        max_relationships_per_type: int = 5
    ) -> Dict[str, int]:
        """
        Create intelligent relationships based on comprehensive analysis
        """
        relationships = self.analyze_note_relationships(note_id, embedding)
        created_counts = defaultdict(int)
        
        # Create relationships with limits to avoid over-connecting
        for rel_category, rel_list in relationships.items():
            if rel_category == 'weak':
                continue  # Skip weak relationships for now
            
            # Sort by score and take top N
            sorted_rels = sorted(rel_list, key=lambda x: x['score'], reverse=True)
            top_rels = sorted_rels[:max_relationships_per_type]
            
            for rel in top_rels:
                try:
                    rel_type = rel['type']
                    target_id = rel['note_id']
                    
                    # Create bidirectional relationship
                    create_relationship(note_id, target_id, rel_type=rel_type)
                    create_relationship(target_id, note_id, rel_type=rel_type)
                    
                    created_counts[rel_type] += 1
                    
                    logger.info(f"Created {rel_type} relationship: {note_id} <-> {target_id} "
                               f"(score: {rel['score']:.3f})")
                    
                except Exception as e:
                    logger.error(f"Error creating relationship {rel_type}: {e}")
        
        return dict(created_counts)

# Global instance
advanced_analyzer = AdvancedSimilarityAnalyzer()
