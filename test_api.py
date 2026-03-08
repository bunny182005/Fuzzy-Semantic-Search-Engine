#!/usr/bin/env python3
"""
API Test Script

Tests all endpoints of the semantic search API.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200
    print("✓ Health check passed")

def test_query(query_text):
    """Test query endpoint."""
    print(f"\nQuerying: '{query_text}'")
    
    response = requests.post(
        f"{BASE_URL}/query",
        json={"query": query_text}
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    print(f"Cache Hit: {result['cache_hit']}")
    if result['cache_hit']:
        print(f"  Matched Query: '{result['matched_query']}'")
        print(f"  Similarity: {result['similarity_score']:.4f}")
    print(f"Dominant Cluster: {result['dominant_cluster']}")
    print(f"Processing Time: {result['processing_time_ms']:.2f}ms")
    
    if not result['cache_hit']:
        print(f"Results: {len(result['result']['documents'])} documents")
        if result['result']['documents']:
            print(f"Top result preview: {result['result']['documents'][0][:100]}...")
    
    assert response.status_code == 200
    return result

def test_cache_stats():
    """Test cache stats endpoint."""
    print("\n" + "="*80)
    print("Cache Statistics")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/cache/stats")
    print(f"Status: {response.status_code}")
    stats = response.json()
    
    print(json.dumps(stats, indent=2))
    
    assert response.status_code == 200
    return stats

def test_cache_clear():
    """Test cache clear endpoint."""
    print("\n" + "="*80)
    print("TEST: Clear Cache")
    print("="*80)
    
    response = requests.delete(f"{BASE_URL}/cache")
    print(f"Status: {response.status_code}")
    result = response.json()
    
    print(f"Message: {result['message']}")
    print(f"Entries Cleared: {result['entries_cleared']}")
    
    assert response.status_code == 200
    print("✓ Cache cleared")

def main():
    """Run all tests."""
    print("="*80)
    print("SEMANTIC SEARCH API - TEST SUITE")
    print("="*80)
    print(f"Testing API at: {BASE_URL}")
    print("Make sure the server is running: uvicorn main:app --host 0.0.0.0 --port 8000")
    print("="*80)
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Clear cache to start fresh
        test_cache_clear()
        
        # Test 3: Query (should be cache miss)
        print("\n" + "="*80)
        print("TEST 2: Query (Cache Miss)")
        print("="*80)
        result1 = test_query("space shuttle mission to mars")
        assert not result1['cache_hit'], "Expected cache miss"
        print("✓ Query processed (cache miss as expected)")
        
        # Test 4: Similar query (should be cache hit)
        print("\n" + "="*80)
        print("TEST 3: Similar Query (Cache Hit)")
        print("="*80)
        time.sleep(0.5)  # Small delay
        result2 = test_query("spacecraft launch mission")
        # May or may not hit depending on similarity
        print("✓ Query processed")
        
        # Test 5: Different query (should be cache miss)
        print("\n" + "="*80)
        print("TEST 4: Different Query (Cache Miss)")
        print("="*80)
        result3 = test_query("baseball game score")
        print("✓ Query processed")
        
        # Test 6: Exact repeat (should definitely hit)
        print("\n" + "="*80)
        print("TEST 5: Exact Repeat (Cache Hit)")
        print("="*80)
        result4 = test_query("space shuttle mission to mars")
        assert result4['cache_hit'], "Expected cache hit on exact repeat"
        assert result4['similarity_score'] == 1.0, "Expected perfect similarity"
        print("✓ Exact match cache hit confirmed")
        
        # Test 7: Cache stats
        stats = test_cache_stats()
        print(f"\n✓ Total queries processed: {stats['total_queries']}")
        print(f"✓ Hit rate: {stats['hit_rate']:.2%}")
        
        # Test 8: More queries to build cache
        print("\n" + "="*80)
        print("TEST 6: Multiple Queries")
        print("="*80)
        
        queries = [
            "computer graphics rendering",
            "gun control legislation",
            "NASA budget cuts",
            "encrypted email privacy",
            "baseball match results"  # Similar to earlier query
        ]
        
        for query in queries:
            result = test_query(query)
        
        # Final stats
        final_stats = test_cache_stats()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print("✓ All tests passed!")
        print(f"✓ Cache entries: {final_stats['total_entries']}")
        print(f"✓ Hit rate: {final_stats['hit_rate']:.2%}")
        print(f"✓ Similarity threshold: {final_stats['similarity_threshold']}")
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to API")
        print("Make sure the server is running:")
        print("  cd src")
        print("  uvicorn main:app --host 0.0.0.0 --port 8000")
        return 1
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
