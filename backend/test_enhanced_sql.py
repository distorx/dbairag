#!/usr/bin/env python3
"""
Test script to verify enhanced SQL generation with full metadata usage
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8001/api/queries/execute-optimized"

# Test queries that require understanding of database metadata
test_queries = [
    # Simple counts
    {"name": "Count Students", "query": "count students"},
    {"name": "Count Cities", "query": "count cities"},
    
    # Queries requiring relationships
    {"name": "Students with Family", "query": "count students with family members"},
    {"name": "Students from Cities", "query": "show students with their city names"},
    {"name": "Family Members by Student", "query": "show family members for each student"},
    
    # Queries requiring index awareness
    {"name": "Students by Status", "query": "count students by application status"},
    {"name": "Active Records", "query": "show active students"},
    
    # Complex queries requiring full metadata
    {"name": "Students with Dependencies", "query": "show students with their family members and cities"},
    {"name": "Application Summary", "query": "show scholarship applications with student names"},
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
        
        return {
            "success": True,
            "sql": result.get("generated_sql", result.get("sql_query", "")),
            "execution_time": result.get("execution_time", 0),
            "metadata": result.get("metadata", {}),
            "row_count": len(result.get("results", [])) if result.get("results") else 0,
            "sample_results": result.get("results", [])[:3]  # First 3 rows
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("Testing Enhanced SQL Generation with Full Metadata")
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
            # Format SQL for readability
            sql = result['sql']
            if sql:
                # Basic formatting
                sql = sql.replace("SELECT", "\n  SELECT")
                sql = sql.replace("FROM", "\n  FROM")
                sql = sql.replace("WHERE", "\n  WHERE")
                sql = sql.replace("JOIN", "\n  JOIN")
                sql = sql.replace("GROUP BY", "\n  GROUP BY")
                sql = sql.replace("ORDER BY", "\n  ORDER BY")
            print(f"{sql}")
            
            print(f"\nExecution Time: {result['execution_time']:.3f}s")
            print(f"Rows Returned: {result['row_count']}")
            
            # Show metadata if available
            metadata = result.get('metadata', {})
            if metadata:
                method = metadata.get('method', 'unknown')
                print(f"Method Used: {method}")
                if 'relationships_used' in metadata:
                    print(f"Relationships: {metadata['relationships_used']}")
                if 'indexes_used' in metadata:
                    print(f"Indexes: {metadata['indexes_used']}")
            
            if result['sample_results']:
                print("\nSample Results:")
                for i, row in enumerate(result['sample_results'], 1):
                    print(f"  Row {i}: {json.dumps(row, indent=2)}")
        else:
            print(f"✗ Error: {result['error']}")
        
        print()
        print("=" * 80)
        print()

if __name__ == "__main__":
    main()