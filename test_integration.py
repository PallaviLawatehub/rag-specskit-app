#!/usr/bin/env python
"""Integration test for RAG system: upload → query → reset."""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint."""
    print("\n[1] Testing /healthz endpoint...")
    resp = requests.get(f"{BASE_URL}/healthz")
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    return resp.status_code == 200

def test_upload():
    """Test upload endpoint."""
    print("\n[2] Testing /api/upload endpoint...")
    
    # Create test file
    test_file = Path("test.txt")
    test_file.write_text("""This is a test document about machine learning.
Machine learning is a subset of artificial intelligence.
It focuses on learning from data without being explicitly programmed.
Deep learning uses neural networks for pattern recognition.
Natural language processing helps computers understand human language.""")
    
    # Upload
    with open(test_file, 'rb') as f:
        files = {'file': f}
        resp = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw: {resp.text}")
        return False

def test_query():
    """Test query endpoint."""
    print("\n[3] Testing /api/query endpoint...")
    
    payload = {
        "query": "machine learning",
        "top_k": 3
    }
    resp = requests.post(f"{BASE_URL}/api/query", json=payload)
    
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw: {resp.text}")
        return False

def test_reset():
    """Test reset endpoint."""
    print("\n[4] Testing /api/reset endpoint...")
    
    resp = requests.delete(f"{BASE_URL}/api/reset")
    
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Raw: {resp.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("RAG System Integration Test")
    print("=" * 60)
    
    results = {
        "health": test_health(),
        "upload": test_upload(),
        "query": test_query(),
        "reset": test_reset(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:15} {status}")
    
    all_passed = all(results.values())
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed!"))
