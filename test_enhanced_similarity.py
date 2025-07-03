#!/usr/bin/env python3
"""
Test script for enhanced similarity system
Demonstrates the improvements over basic cosine similarity
"""

import requests
import json
import time
from typing import Dict, List

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_similarity_improvements():
    """Test the enhanced similarity system with sample notes"""
    
    print("🧪 Testing Enhanced Similarity System")
    print("=" * 50)
    
    # Sample notes for testing
    test_notes = [
        {
            "title": "Introduction to Machine Learning",
            "content": """
            # Introduction to Machine Learning
            
            Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.
            
            ## Key Concepts
            - Supervised learning
            - Unsupervised learning
            - Neural networks
            - Training data
            
            This is a foundational topic that should be understood before diving into advanced topics.
            """
        },
        {
            "title": "Neural Networks Deep Dive",
            "content": """
            # Neural Networks Deep Dive
            
            Neural networks are computing systems inspired by biological neural networks. They are the foundation of deep learning.
            
            ## Architecture
            - Input layer
            - Hidden layers
            - Output layer
            - Activation functions
            
            **Prerequisites**: Understanding of machine learning basics is required.
            
            ## Code Example
            ```python
            import tensorflow as tf
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dense(10, activation='softmax')
            ])
            ```
            """
        },
        {
            "title": "Python Programming Basics",
            "content": """
            # Python Programming Basics
            
            Python is a high-level programming language known for its simplicity and readability.
            
            ## Basic Syntax
            - Variables and data types
            - Control structures
            - Functions
            - Classes and objects
            
            ## Code Example
            ```python
            def hello_world():
                print("Hello, World!")
                
            hello_world()
            ```
            
            This is an introductory guide for beginners.
            """
        },
        {
            "title": "Advanced Python Techniques",
            "content": """
            # Advanced Python Techniques
            
            After mastering Python basics, you can explore advanced concepts.
            
            ## Advanced Topics
            - Decorators
            - Context managers
            - Metaclasses
            - Async programming
            
            ## Code Example
            ```python
            @decorator
            def advanced_function():
                with context_manager():
                    return async_operation()
            ```
            
            **Prerequisites**: Solid understanding of Python basics required.
            """
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
    
    print(f"\n🔍 Testing similarity analysis...")
    
    # Test 1: Basic similarity comparison
    print("\n1. Basic vs Enhanced Similarity Comparison")
    print("-" * 40)
    
    test_note = created_notes[0]  # ML intro note
    note_id = test_note['id']
    
    # Get basic similarity
    try:
        basic_response = requests.get(f"{API_BASE_URL}/notes/{note_id}/similar?top_k=3")
        if basic_response.status_code == 200:
            basic_similar = basic_response.json()
            print("Basic similarity results:")
            for sim in basic_similar:
                target_note = next((n for n in created_notes if n['id'] == sim['id']), None)
                if target_note:
                    print(f"  - {target_note['title']}: {sim['score']:.3f}")
        else:
            print(f"❌ Basic similarity failed: {basic_response.status_code}")
    except Exception as e:
        print(f"❌ Error getting basic similarity: {e}")
    
    # Get enhanced analysis
    try:
        enhanced_response = requests.get(f"{API_BASE_URL}/notes/{note_id}/analyze?config_name=default")
        if enhanced_response.status_code == 200:
            analysis = enhanced_response.json()
            print("\nEnhanced analysis results:")
            
            for category, relationships in analysis.items():
                if relationships:
                    print(f"  {category.upper()}:")
                    for rel in relationships[:2]:  # Show top 2
                        target_note = next((n for n in created_notes if n['id'] == rel['id']), None)
                        if target_note:
                            print(f"    - {target_note['title']}: {rel['score']:.3f} ({rel['relationship_type']})")
        else:
            print(f"❌ Enhanced analysis failed: {enhanced_response.status_code}")
    except Exception as e:
        print(f"❌ Error getting enhanced analysis: {e}")
    
    # Test 2: Different configurations
    print("\n2. Testing Different Configurations")
    print("-" * 40)
    
    configs_to_test = ['default', 'semantic_focused', 'keyword_focused', 'strict']
    
    for config_name in configs_to_test:
        try:
            config_response = requests.post(
                f"{API_BASE_URL}/notes/{note_id}/link-enhanced",
                json={"config_name": config_name}
            )
            if config_response.status_code == 200:
                result = config_response.json()
                print(f"{config_name}: {result['total_relationships']} relationships")
                for rel_type, count in result['relationships_created'].items():
                    print(f"  - {rel_type}: {count}")
            else:
                print(f"❌ Config {config_name} failed: {config_response.status_code}")
        except Exception as e:
            print(f"❌ Error testing config {config_name}: {e}")
    
    # Test 3: Custom configuration
    print("\n3. Testing Custom Configuration")
    print("-" * 40)
    
    custom_config = {
        "semantic_weight": 0.6,
        "keyword_weight": 0.2,
        "structural_weight": 0.1,
        "topic_weight": 0.1,
        "min_threshold": 0.4
    }
    
    try:
        custom_response = requests.post(
            f"{API_BASE_URL}/notes/{note_id}/link-enhanced",
            json=custom_config
        )
        if custom_response.status_code == 200:
            result = custom_response.json()
            print(f"Custom config: {result['total_relationships']} relationships")
            for rel_type, count in result['relationships_created'].items():
                print(f"  - {rel_type}: {count}")
        else:
            print(f"❌ Custom config failed: {custom_response.status_code}")
    except Exception as e:
        print(f"❌ Error testing custom config: {e}")
    
    # Test 4: Available configurations
    print("\n4. Available Configurations")
    print("-" * 40)
    
    try:
        configs_response = requests.get(f"{API_BASE_URL}/similarity/configs")
        if configs_response.status_code == 200:
            configs_info = configs_response.json()
            print("Available configurations:")
            for config_name in configs_info['available_configs']:
                description = configs_info['config_descriptions'].get(config_name, 'No description')
                print(f"  - {config_name}: {description}")
        else:
            print(f"❌ Failed to get configs: {configs_response.status_code}")
    except Exception as e:
        print(f"❌ Error getting configs: {e}")
    
    print("\n✅ Enhanced similarity testing completed!")
    print("\nKey Improvements Demonstrated:")
    print("- Multiple similarity measures (semantic, keyword, structural, topic)")
    print("- Different relationship types with semantic meaning")
    print("- Configurable weights and thresholds")
    print("- Hierarchical and sequential relationship detection")
    print("- Flexible configuration profiles for different use cases")

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
    print("🚀 Starting Enhanced Similarity Test")
    print("Make sure your API server is running on http://localhost:8000")
    
    # Wait a moment for user to confirm
    input("Press Enter to continue...")
    
    try:
        test_similarity_improvements()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    
    # Ask if user wants to cleanup
    cleanup = input("\nClean up test notes? (y/N): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_notes()
    
    print("\n👋 Test completed!")
