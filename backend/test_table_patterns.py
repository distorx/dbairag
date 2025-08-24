#!/usr/bin/env python3
"""
Test script to verify pattern matching for all table names
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8001/api/queries/execute-optimized"

# Test queries for various table names with clear naming conventions
test_queries = [
    # Tables with CamelCase that should be matched
    {"name": "ScholarshipApplications", "query": "count scholarship applications"},
    {"name": "StudentRecommendeds", "query": "count student recommendeds"},
    {"name": "StudentDependents", "query": "count student dependents"},
    {"name": "FamilyMembers", "query": "count family members"},
    {"name": "HighSchools", "query": "count high schools"},
    {"name": "HighSchools (alt)", "query": "count highschools"},
    
    # Single word tables
    {"name": "Cities", "query": "count cities"},
    {"name": "Regions", "query": "count regions"},
    {"name": "Occupations", "query": "count occupations"},
    {"name": "Municipios", "query": "count municipios"},
    {"name": "Students", "query": "count students"},
    {"name": "Answers", "query": "count answers"},
    {"name": "Questions", "query": "count questions"},
    {"name": "Profiles", "query": "count profiles"},
    
    # Tables with prefixes
    {"name": "StudentAnswers", "query": "count student answers"},
    {"name": "StudentProfiles", "query": "count student profiles"},
    
    # Edge cases
    {"name": "Student (singular)", "query": "count student"},
    {"name": "City (singular)", "query": "count city"},
    {"name": "Region (singular)", "query": "count region"},
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
            "row_count": result.get("results", [{}])[0].get("total", 0) if result.get("results") else 0,
            "full_response": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("Testing Pattern Matching for Table Names")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for test in test_queries:
        print(f"Test: {test['name']}")
        print(f"Query: '{test['query']}'")
        
        result = test_query(test['query'])
        
        if result['success']:
            sql = result['sql']
            # Check if the SQL contains a valid table name
            if sql and "SELECT COUNT(*)" in sql and "FROM" in sql:
                table_in_sql = sql.split("FROM")[1].split("WITH")[0].strip()
                print(f"✓ Success! SQL: {sql}")
                print(f"  Table: {table_in_sql}, Count: {result['row_count']}")
                passed += 1
            else:
                print(f"✗ Unexpected SQL: {sql}")
                failed += 1
        else:
            print(f"✗ Error: {result['error']}")
            failed += 1
        
        print("-" * 40)
    
    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_queries)} tests")
    print("=" * 80)

if __name__ == "__main__":
    main()