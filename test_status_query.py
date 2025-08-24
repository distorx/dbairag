#!/usr/bin/env python3
"""Test script to verify status filtering in student application queries"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000/api"

# Test queries with different statuses
test_queries = [
    "count students with application",  # Should return all 305
    "count students with application rejected",  # Should filter by rejected status (5)
    "count students with application approved",  # Should filter by approved status (4)
    "count students with application pending",  # Should filter by pending status (1)
    "count students with application submitted",  # Should filter by submitted status (2)
]

def test_query(prompt):
    """Test a single query"""
    print(f"\n{'='*60}")
    print(f"Testing: {prompt}")
    print('='*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/queries/execute",
            json={
                "connection_id": 1,
                "prompt": prompt
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Show the generated SQL
            if 'generated_sql' in result:
                print(f"Generated SQL: {result['generated_sql']}")
            
            # Show the result
            if 'result_data' in result:
                if isinstance(result['result_data'], dict) and 'data' in result['result_data']:
                    data = result['result_data']['data']
                    if data and len(data) > 0:
                        print(f"Result: {data[0]}")
                    else:
                        print("Result: No data returned")
                else:
                    print(f"Result: {result['result_data']}")
            
            # Check if WHERE clause is present for status queries
            if 'generated_sql' in result:
                sql = result['generated_sql']
                if any(status in prompt.lower() for status in ['rejected', 'approved', 'pending', 'submitted']):
                    if 'WHERE' in sql and 'Status' in sql:
                        print("✅ Status filter correctly applied")
                    else:
                        print("❌ Status filter NOT applied - query may return incorrect results")
                        
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Testing RAG SQL Query Status Filtering")
    print("="*60)
    
    # Test each query
    for query in test_queries:
        test_query(query)
    
    print("\n" + "="*60)
    print("Test complete!")

if __name__ == "__main__":
    main()
