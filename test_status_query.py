#!/usr/bin/env python3
"""
Test script to demonstrate counting students by application status with totals
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8001/api/queries/execute-optimized"

# Test queries for counting students by application status
test_queries = [
    {
        "name": "Basic count by status",
        "query": "count students by application status"
    },
    {
        "name": "Count with total",
        "query": "count students by application status with total"
    },
    {
        "name": "Group by with total",
        "query": "show count of students grouped by application status including total"
    },
    {
        "name": "Detailed with all statuses",
        "query": "count students for each status draft, submitted, approved, rejected, cancelled and show total"
    },
    {
        "name": "Alternative phrasing",
        "query": "how many students have each application status and what is the total count"
    }
]

def test_query(query_text, connection_id=1):
    """Execute a test query and return the result"""
    payload = {
        "prompt": query_text,
        "connection_id": connection_id
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Debug print full response
        print(f"DEBUG - Full response: {json.dumps(result, indent=2)}")
        
        return {
            "success": True,
            "sql": result.get("generated_sql", result.get("sql_query", "")),
            "execution_time": result.get("execution_time", 0),
            "row_count": len(result.get("results", [])) if result.get("results") else 0,
            "results": result.get("results", [])[:5],  # First 5 rows
            "full_response": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("Testing Student Count by Application Status Queries")
    print("=" * 80)
    print()
    
    for test in test_queries:
        print(f"Test: {test['name']}")
        print(f"Query: '{test['query']}'")
        print("-" * 40)
        
        result = test_query(test['query'])
        
        if result['success']:
            print(f"✓ Success!")
            print(f"SQL Generated:")
            print(f"  {result['sql']}")
            print(f"Execution Time: {result['execution_time']:.3f}s")
            print(f"Rows Returned: {result['row_count']}")
            if result['results']:
                print("Sample Results:")
                for row in result['results']:
                    print(f"  {row}")
        else:
            print(f"✗ Error: {result['error']}")
        
        print()
        print("=" * 80)
        print()

if __name__ == "__main__":
    main()