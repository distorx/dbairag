#!/usr/bin/env python3
"""
Test SQL generation with OpenAI using full database metadata
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8001/api/queries/execute-optimized"

# Test queries that demonstrate full metadata usage
test_queries = [
    # Simple table queries
    {"name": "Count Students", "query": "count all students"},
    {"name": "Count Cities", "query": "count all cities"},
    {"name": "Count Family Members", "query": "count family members"},
    
    # Queries requiring relationships (foreign keys)
    {"name": "Students with Families", "query": "show students who have family members"},
    {"name": "Students by City", "query": "show students with their city names"},
    
    # Queries using indexes and primary keys
    {"name": "Active Students", "query": "show all active students"},
    {"name": "Students by Status", "query": "count students grouped by application status"},
    
    # Complex queries requiring full metadata understanding
    {"name": "Complete Student Info", "query": "show students with their cities and family members count"},
    {"name": "Application Summary", "query": "show scholarship applications with student names and status"},
]

def test_query(query_text, connection_id=1):
    """Execute a test query and return the result"""
    payload = {
        "prompt": query_text,
        "connection_id": connection_id
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": True,
            "sql": result.get("generated_sql", result.get("sql_query", "")),
            "execution_time": result.get("execution_time", 0),
            "metadata": result.get("metadata", {}),
            "row_count": len(result.get("results", [])) if result.get("results") else 0,
            "error": result.get("error")
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout (>30s)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("TESTING SQL GENERATION WITH OPENAI + FULL METADATA")
    print("=" * 80)
    print()
    
    successful = 0
    failed = 0
    
    for test in test_queries:
        print(f"Test: {test['name']}")
        print(f"Query: '{test['query']}'")
        print("-" * 40)
        
        result = test_query(test['query'])
        
        if result['success']:
            if result.get('sql'):
                print(f"✓ SQL Generated Successfully!")
                
                # Format SQL for readability
                sql = result['sql']
                if sql:
                    # Add line breaks for readability
                    sql = sql.replace(" FROM ", "\n  FROM ")
                    sql = sql.replace(" WHERE ", "\n  WHERE ")
                    sql = sql.replace(" JOIN ", "\n  JOIN ")
                    sql = sql.replace(" INNER JOIN ", "\n  INNER JOIN ")
                    sql = sql.replace(" LEFT JOIN ", "\n  LEFT JOIN ")
                    sql = sql.replace(" GROUP BY ", "\n  GROUP BY ")
                    sql = sql.replace(" ORDER BY ", "\n  ORDER BY ")
                    sql = sql.replace(" WITH ", " WITH ")
                
                print(f"SQL:\n  {sql}")
                
                # Show method used
                metadata = result.get('metadata', {})
                method = metadata.get('method', 'unknown')
                print(f"\nMethod: {method}")
                
                if method == 'llm_optimized':
                    print(f"LLM Time: {metadata.get('llm_time', 'N/A')}")
                    print(f"Total Time: {metadata.get('total_time', 'N/A')}")
                elif method == 'pattern_matching':
                    print(f"Pattern Match Time: {metadata.get('pattern_match_time', 'N/A')}")
                
                print(f"Execution Time: {result['execution_time']:.3f}s")
                print(f"Rows Returned: {result['row_count']}")
                successful += 1
            else:
                print(f"✗ No SQL generated")
                if result.get('error'):
                    print(f"Error: {result['error']}")
                failed += 1
        else:
            print(f"✗ Request Failed: {result['error']}")
            failed += 1
        
        print()
        print("=" * 80)
        print()
    
    # Summary
    print("SUMMARY")
    print("-" * 40)
    print(f"Total Tests: {len(test_queries)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/len(test_queries)*100):.1f}%")

if __name__ == "__main__":
    main()