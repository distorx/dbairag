#!/usr/bin/env python3
"""
Test the fuzzy matching functionality via the API.
This tests that the system correctly handles misspelled table names.
"""
import requests
import json
import time

API_URL = "http://localhost:8000/api"

def test_fuzzy_matching():
    """Test fuzzy matching with various queries"""
    
    print("Testing Fuzzy Matching via API")
    print("=" * 70)
    
    # Test queries with connection ID 3 (test_empty_tables database)
    test_queries = [
        {
            "connection_id": 3,
            "prompt": "count city",  # Should use 'cities' (has data)
            "expected_table": "cities"
        },
        {
            "connection_id": 3,
            "prompt": "count product",  # Should use 'products' (has data)
            "expected_table": "products"
        },
        {
            "connection_id": 3,
            "prompt": "count customer",  # Should use 'customer' (has data)
            "expected_table": "customer"
        },
        {
            "connection_id": 3,
            "prompt": "select * from citi",  # Misspelling - should use 'cities'
            "expected_table": "cities"
        }
    ]
    
    for test in test_queries:
        print(f"\nTest: '{test['prompt']}' (expecting table: {test['expected_table']})")
        print("-" * 60)
        
        response = requests.post(
            f"{API_URL}/queries/execute",
            json={
                "connection_id": test["connection_id"],
                "prompt": test["prompt"]
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if the correct table was used
            generated_sql = result.get("generated_sql", "")
            print(f"  Generated SQL: {generated_sql}")
            
            if test["expected_table"].lower() in generated_sql.lower():
                print(f"  ✅ Correctly used table: {test['expected_table']}")
            else:
                print(f"  ❌ Did not use expected table: {test['expected_table']}")
            
            # Show the result
            if result.get("result_type") == "text":
                print(f"  Result: {result.get('result_data', 'N/A')}")
            elif result.get("result_type") == "table":
                data = json.loads(result.get("result_data", "[]"))
                print(f"  Result: {len(data)} rows")
                if data and len(data) > 0:
                    print(f"  Sample: {data[0]}")
        else:
            print(f"  ❌ Error: {response.status_code}")
            print(f"  Response: {response.text}")
        
        time.sleep(1)  # Small delay between requests
    
    print("\n" + "=" * 70)
    print("Test completed!")

if __name__ == "__main__":
    test_fuzzy_matching()