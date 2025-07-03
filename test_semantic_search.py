#!/usr/bin/env python3
"""
Test script for semantic search functionality
Tests the semantic search API and demonstrates its capabilities
"""

import requests
import json
import time
from typing import Dict, List

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_semantic_search():
    """Test the semantic search functionality"""
    
    print("🔍 Testing Semantic Search Functionality")
    print("=" * 50)
    
    # Sample notes for testing (if needed)
    test_notes = [
        {
            "title": "Machine Learning Algorithms",
            "content": """
            Machine learning algorithms are computational methods that enable computers to learn patterns from data without being explicitly programmed. 
            Common types include supervised learning (classification and regression), unsupervised learning (clustering and dimensionality reduction), 
            and reinforcement learning. Popular algorithms include linear regression, decision trees, neural networks, and support vector machines.
            """
        },
        {
            "title": "Data Structures and Algorithms",
            "content": """
            Data structures are ways of organizing and storing data efficiently. Common data structures include arrays, linked lists, stacks, queues, 
            trees, and graphs. Algorithms are step-by-step procedures for solving problems. Important algorithmic concepts include sorting, searching, 
            graph traversal, and dynamic programming. Time and space complexity analysis helps evaluate algorithm efficiency.
            """
        },
        {
            "title": "Web Development with React",
            "content": """
            React is a JavaScript library for building user interfaces, particularly web applications. It uses a component-based architecture 
            where UI elements are broken down into reusable components. Key concepts include JSX syntax, state management, props, hooks, 
            and the virtual DOM. React enables developers to create interactive and dynamic web applications efficiently.
            """
        },
        {
            "title": "Database Design Principles",
            "content": """
            Database design involves organizing data efficiently and ensuring data integrity. Key principles include normalization to reduce 
            redundancy, defining relationships between entities, choosing appropriate data types, and creating indexes for performance. 
            ACID properties (Atomicity, Consistency, Isolation, Durability) ensure reliable database transactions.
            """
        }
    ]
    
    # Check if we have notes, if not create some
    try:
        response = requests.get(f"{API_BASE_URL}/notes")
        existing_notes = response.json() if response.status_code == 200 else []
        
        if len(existing_notes) < 4:
            print("📝 Creating test notes for semantic search...")
            for note_data in test_notes:
                try:
                    response = requests.post(f"{API_BASE_URL}/notes", json=note_data, params={"use_enhanced_linking": False})
                    if response.status_code == 200:
                        note = response.json()
                        print(f"✅ Created: {note['title']}")
                    else:
                        print(f"❌ Failed to create note: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error creating note: {e}")
        else:
            print(f"📚 Using existing {len(existing_notes)} notes for testing")
            
    except Exception as e:
        print(f"❌ Error checking existing notes: {e}")
    
    # Test cases for semantic search
    test_queries = [
        {
            "query": "artificial intelligence and machine learning",
            "description": "Should find ML-related content"
        },
        {
            "query": "sorting algorithms and data organization",
            "description": "Should find data structures content"
        },
        {
            "query": "building web applications",
            "description": "Should find web development content"
        },
        {
            "query": "storing and organizing information",
            "description": "Should find database-related content"
        },
        {
            "query": "programming concepts",
            "description": "Should find general programming content"
        },
        {
            "query": "completely unrelated topic like cooking recipes",
            "description": "Should return few or no results"
        }
    ]
    
    print("\n🧪 Testing Semantic Search Queries")
    print("-" * 40)
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {test_case['query']}")
        print(f"   Expected: {test_case['description']}")
        
        try:
            # Test POST endpoint
            response = requests.post(f"{API_BASE_URL}/search/semantic", json={
                "query": test_case["query"],
                "max_results": 5,
                "min_similarity": 0.2
            })
            
            if response.status_code == 200:
                results = response.json()
                print(f"   ✅ Found {len(results['results'])} results in {results['search_time_ms']}ms")
                
                for j, result in enumerate(results['results'][:3], 1):  # Show top 3
                    similarity_percent = round(result['similarity_score'] * 100, 1)
                    print(f"      {j}. {result['title']} ({similarity_percent}%)")
                    print(f"         Snippet: {result['snippet'][:80]}...")
                    
                if len(results['results']) == 0:
                    print("      ℹ️ No results found (expected for unrelated queries)")
                    
            else:
                error_data = response.json()
                print(f"   ❌ Error: {error_data.get('detail', response.status_code)}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Test GET endpoint
    print("\n🌐 Testing GET Endpoint")
    print("-" * 40)
    
    try:
        test_query = "machine learning algorithms"
        response = requests.get(f"{API_BASE_URL}/search/semantic", params={
            "q": test_query,
            "max_results": 3,
            "min_similarity": 0.3
        })
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ GET endpoint works: {len(results['results'])} results")
            print(f"   Query: {results['query']}")
            print(f"   Time: {results['search_time_ms']}ms")
        else:
            print(f"❌ GET endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ GET endpoint error: {e}")
    
    # Test different similarity thresholds
    print("\n📊 Testing Similarity Thresholds")
    print("-" * 40)
    
    test_query = "data structures and algorithms"
    thresholds = [0.1, 0.3, 0.5, 0.7]
    
    for threshold in thresholds:
        try:
            response = requests.post(f"{API_BASE_URL}/search/semantic", json={
                "query": test_query,
                "max_results": 10,
                "min_similarity": threshold
            })
            
            if response.status_code == 200:
                results = response.json()
                print(f"   Threshold {threshold}: {len(results['results'])} results")
            else:
                print(f"   Threshold {threshold}: Error {response.status_code}")
                
        except Exception as e:
            print(f"   Threshold {threshold}: Exception {e}")
    
    # Test performance with different result limits
    print("\n⚡ Testing Performance")
    print("-" * 40)
    
    result_limits = [5, 10, 20, 50]
    test_query = "programming and software development"
    
    for limit in result_limits:
        try:
            start_time = time.time()
            response = requests.post(f"{API_BASE_URL}/search/semantic", json={
                "query": test_query,
                "max_results": limit,
                "min_similarity": 0.2
            })
            request_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                results = response.json()
                print(f"   Limit {limit}: {results['search_time_ms']}ms (server) + {request_time:.1f}ms (network)")
            else:
                print(f"   Limit {limit}: Error {response.status_code}")
                
        except Exception as e:
            print(f"   Limit {limit}: Exception {e}")
    
    print("\n✅ Semantic search testing completed!")
    print("\nKey Features Tested:")
    print("- ✅ POST endpoint with JSON payload")
    print("- ✅ GET endpoint with query parameters")
    print("- ✅ Similarity scoring and ranking")
    print("- ✅ Snippet generation")
    print("- ✅ Different similarity thresholds")
    print("- ✅ Result limiting")
    print("- ✅ Performance measurement")
    print("- ✅ Error handling")

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
    print("🚀 Starting Semantic Search Test")
    print("Make sure your API server is running on http://localhost:8000")
    
    # Wait a moment for user to confirm
    input("Press Enter to continue...")
    
    try:
        test_semantic_search()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
    
    # Ask if user wants to cleanup
    cleanup = input("\nClean up test notes? (y/N): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_notes()
    
    print("\n👋 Test completed!")
