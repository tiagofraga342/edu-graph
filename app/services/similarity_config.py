# similarity_config.py
"""
Configuration for similarity analysis and knowledge graph construction
"""

from typing import Dict, Any
from dataclasses import dataclass, field

@dataclass
class SimilarityConfig:
    """Configuration for similarity analysis"""
    
    # Weights for different similarity measures
    semantic_weight: float = 0.4
    keyword_weight: float = 0.3
    structural_weight: float = 0.15
    topic_weight: float = 0.15
    
    # Thresholds for relationship creation
    highly_related_threshold: float = 0.8
    semantically_related_threshold: float = 0.7
    topically_related_threshold: float = 0.6
    structurally_related_threshold: float = 0.6
    keyword_related_threshold: float = 0.6
    loosely_related_threshold: float = 0.5
    
    # Advanced analysis settings
    concept_overlap_threshold: float = 0.3
    hierarchical_containment_threshold: float = 0.8
    sequential_pattern_threshold: int = 2
    
    # Relationship limits
    max_relationships_per_type: int = 5
    max_total_relationships: int = 20
    
    # Feature flags
    enable_hierarchical_detection: bool = True
    enable_sequential_detection: bool = True
    enable_concept_analysis: bool = True
    enable_weak_relationships: bool = False
    
    def get_weights(self) -> Dict[str, float]:
        """Get similarity weights as dictionary"""
        return {
            'semantic': self.semantic_weight,
            'keyword': self.keyword_weight,
            'structural': self.structural_weight,
            'topic': self.topic_weight
        }
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get relationship thresholds as dictionary"""
        return {
            'HIGHLY_RELATED': self.highly_related_threshold,
            'SEMANTICALLY_RELATED': self.semantically_related_threshold,
            'TOPICALLY_RELATED': self.topically_related_threshold,
            'STRUCTURALLY_RELATED': self.structurally_related_threshold,
            'KEYWORD_RELATED': self.keyword_related_threshold,
            'LOOSELY_RELATED': self.loosely_related_threshold
        }

# Predefined configurations for different use cases
CONFIGS = {
    'default': SimilarityConfig(),
    
    'semantic_focused': SimilarityConfig(
        semantic_weight=0.6,
        keyword_weight=0.2,
        structural_weight=0.1,
        topic_weight=0.1,
        semantically_related_threshold=0.6
    ),
    
    'keyword_focused': SimilarityConfig(
        semantic_weight=0.2,
        keyword_weight=0.5,
        structural_weight=0.15,
        topic_weight=0.15,
        keyword_related_threshold=0.5
    ),
    
    'strict': SimilarityConfig(
        highly_related_threshold=0.85,
        semantically_related_threshold=0.75,
        topically_related_threshold=0.65,
        loosely_related_threshold=0.6,
        max_relationships_per_type=3,
        max_total_relationships=10
    ),
    
    'permissive': SimilarityConfig(
        highly_related_threshold=0.7,
        semantically_related_threshold=0.6,
        topically_related_threshold=0.5,
        loosely_related_threshold=0.4,
        max_relationships_per_type=8,
        max_total_relationships=30,
        enable_weak_relationships=True
    ),
    
    'academic': SimilarityConfig(
        semantic_weight=0.35,
        keyword_weight=0.35,
        structural_weight=0.2,
        topic_weight=0.1,
        enable_hierarchical_detection=True,
        enable_sequential_detection=True,
        concept_overlap_threshold=0.25
    ),
    
    'creative': SimilarityConfig(
        semantic_weight=0.5,
        keyword_weight=0.2,
        structural_weight=0.1,
        topic_weight=0.2,
        semantically_related_threshold=0.6,
        enable_concept_analysis=True
    )
}

def get_config(config_name: str = 'default') -> SimilarityConfig:
    """Get a similarity configuration by name"""
    return CONFIGS.get(config_name, CONFIGS['default'])

def create_custom_config(**kwargs) -> SimilarityConfig:
    """Create a custom configuration with specified parameters"""
    base_config = CONFIGS['default']
    
    # Update with custom parameters
    config_dict = {
        'semantic_weight': kwargs.get('semantic_weight', base_config.semantic_weight),
        'keyword_weight': kwargs.get('keyword_weight', base_config.keyword_weight),
        'structural_weight': kwargs.get('structural_weight', base_config.structural_weight),
        'topic_weight': kwargs.get('topic_weight', base_config.topic_weight),
        'highly_related_threshold': kwargs.get('highly_related_threshold', base_config.highly_related_threshold),
        'semantically_related_threshold': kwargs.get('semantically_related_threshold', base_config.semantically_related_threshold),
        'topically_related_threshold': kwargs.get('topically_related_threshold', base_config.topically_related_threshold),
        'structurally_related_threshold': kwargs.get('structurally_related_threshold', base_config.structurally_related_threshold),
        'keyword_related_threshold': kwargs.get('keyword_related_threshold', base_config.keyword_related_threshold),
        'loosely_related_threshold': kwargs.get('loosely_related_threshold', base_config.loosely_related_threshold),
        'concept_overlap_threshold': kwargs.get('concept_overlap_threshold', base_config.concept_overlap_threshold),
        'hierarchical_containment_threshold': kwargs.get('hierarchical_containment_threshold', base_config.hierarchical_containment_threshold),
        'sequential_pattern_threshold': kwargs.get('sequential_pattern_threshold', base_config.sequential_pattern_threshold),
        'max_relationships_per_type': kwargs.get('max_relationships_per_type', base_config.max_relationships_per_type),
        'max_total_relationships': kwargs.get('max_total_relationships', base_config.max_total_relationships),
        'enable_hierarchical_detection': kwargs.get('enable_hierarchical_detection', base_config.enable_hierarchical_detection),
        'enable_sequential_detection': kwargs.get('enable_sequential_detection', base_config.enable_sequential_detection),
        'enable_concept_analysis': kwargs.get('enable_concept_analysis', base_config.enable_concept_analysis),
        'enable_weak_relationships': kwargs.get('enable_weak_relationships', base_config.enable_weak_relationships)
    }
    
    return SimilarityConfig(**config_dict)

# Default configuration instance
default_config = get_config('default')
