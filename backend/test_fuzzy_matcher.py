#!/usr/bin/env python3
"""
Test script to verify the DynamicFuzzyMatcher prefers tables with data over empty tables.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.dynamic_fuzzy_matcher import DynamicFuzzyMatcher

def test_fuzzy_matcher_with_mock_schema():
    """Test the fuzzy matcher with a mock schema that has empty and populated tables"""
    
    # Create a mock schema similar to our test database
    mock_schema = {
        "tables": {
            "city": {
                "row_count": 0,
                "is_empty": True,
                "columns": [
                    {"name": "id"},
                    {"name": "name"},
                    {"name": "country"},
                    {"name": "population"}
                ]
            },
            "cities": {
                "row_count": 5,
                "is_empty": False,
                "columns": [
                    {"name": "id"},
                    {"name": "name"},
                    {"name": "country"},
                    {"name": "population"}
                ]
            },
            "product": {
                "row_count": 0,
                "is_empty": True,
                "columns": [
                    {"name": "id"},
                    {"name": "name"},
                    {"name": "price"},
                    {"name": "category"}
                ]
            },
            "products": {
                "row_count": 5,
                "is_empty": False,
                "columns": [
                    {"name": "id"},
                    {"name": "name"},
                    {"name": "price"},
                    {"name": "category"}
                ]
            },
            "customer": {
                "row_count": 3,
                "is_empty": False,
                "columns": [
                    {"name": "id"},
                    {"name": "name"},
                    {"name": "email"},
                    {"name": "created_date"}
                ]
            },
            "customers": {
                "row_count": 0,
                "is_empty": True,
                "columns": [
                    {"name": "id"},
                    {"name": "name"},
                    {"name": "email"},
                    {"name": "created_date"}
                ]
            }
        }
    }
    
    # Initialize fuzzy matcher and learn from schema
    matcher = DynamicFuzzyMatcher()
    matcher.learn_from_schema(mock_schema)
    
    print("Testing DynamicFuzzyMatcher - Empty vs Populated Table Preference")
    print("=" * 70)
    print("\nLearned from schema with these tables:")
    for table_name, info in mock_schema["tables"].items():
        status = "EMPTY" if info["is_empty"] else f"POPULATED ({info['row_count']} rows)"
        print(f"  - {table_name}: {status}")
    
    print("\n" + "-" * 70)
    print("Testing fuzzy matching with preference for populated tables:\n")
    
    # Test cases
    test_cases = [
        ("city", "cities"),      # Should choose 'cities' (has data)
        ("product", "products"),  # Should choose 'products' (has data)
        ("customer", "customer"), # Should choose 'customer' (has data)
        ("citi", "cities"),      # Misspelling - should still choose 'cities'
        ("produkt", "products"),  # Misspelling - should still choose 'products'
        ("custumer", "customer"), # Misspelling - should still choose 'customer'
    ]
    
    all_passed = True
    
    for query, expected in test_cases:
        result = matcher.find_best_table_match(query)
        if result:
            matched_table, score = result
            is_empty = mock_schema["tables"][matched_table]["is_empty"]
            row_count = mock_schema["tables"][matched_table]["row_count"]
            status = "EMPTY" if is_empty else f"{row_count} rows"
            
            if matched_table == expected:
                print(f"✅ Query: '{query:10}' → Matched: '{matched_table:10}' (score: {score:3}, {status})")
            else:
                print(f"❌ Query: '{query:10}' → Matched: '{matched_table:10}' (expected: '{expected}')")
                all_passed = False
        else:
            print(f"❌ Query: '{query:10}' → No match found (expected: '{expected}')")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ SUCCESS: All tests passed! Fuzzy matcher correctly prefers tables with data!")
    else:
        print("❌ FAILURE: Some tests failed. Check the logic.")
    
    return all_passed

if __name__ == "__main__":
    success = test_fuzzy_matcher_with_mock_schema()
    sys.exit(0 if success else 1)