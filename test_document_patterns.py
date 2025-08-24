#!/usr/bin/env python3
"""Test script to verify document requirement patterns"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000/api"

# Test queries for document requirements
test_queries = [
    "count students with complete documents",
    "count students ready to be approved",
    "count students ready for approval",
    "count students with all documents",
    "count students with missing documents",
    "count students with incomplete documents",
    "count applications ready for board review",
    "count students with birth certificate",
    "count students with college board results"
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
            
            # Show the generated SQL (truncated)
            if 'generated_sql' in result:
                sql = result['generated_sql']
                if len(sql) > 150:
                    print(f"Generated SQL: {sql[:150]}...")
                else:
                    print(f"Generated SQL: {sql}")
            
            # Show the result
            if 'result_data' in result:
                if isinstance(result['result_data'], dict) and 'data' in result['result_data']:
                    data = result['result_data']['data']
                    if data and len(data) > 0:
                        print(f"✅ Result: {data[0]}")
                    else:
                        print("Result: No data returned")
                else:
                    print(f"Result: {result['result_data']}")
            
            # Check if pattern was detected
            if 'metadata' in result and result['metadata']:
                metadata = result['metadata']
                if 'pattern_type' in metadata:
                    print(f"Pattern Type: {metadata['pattern_type']}")
                        
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            if response.text:
                try:
                    error_detail = response.json()
                    print(f"Error detail: {error_detail.get('detail', response.text)[:200]}")
                except:
                    print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("Testing Document Requirement Patterns")
    print("="*60)
    
    # Test each query
    for query in test_queries:
        test_query(query)
    
    print("\n" + "="*60)
    print("Test complete!")

if __name__ == "__main__":
    main()