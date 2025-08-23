#!/usr/bin/env python3
"""
Standalone test for the DynamicFuzzyMatcher logic to verify it prefers tables with data.
This extracts just the fuzzy matching logic to test without dependencies.
"""
from fuzzywuzzy import fuzz

class SimpleFuzzyMatcher:
    def __init__(self):
        self.actual_tables = []
        self.table_is_empty = {}
        self.table_row_counts = {}
    
    def learn_from_schema(self, schema_info):
        """Learn from database schema"""
        self.actual_tables = list(schema_info["tables"].keys())
        
        for table_name in self.actual_tables:
            table_info = schema_info["tables"][table_name]
            row_count = table_info.get("row_count", 0)
            self.table_row_counts[table_name] = row_count
            self.table_is_empty[table_name] = table_info.get("is_empty", row_count == 0)
    
    def find_best_table_match(self, query_term):
        """Find best matching table, preferring tables with data"""
        if not self.actual_tables:
            return None
        
        query_lower = query_term.lower()
        candidates = []  # List of (table, base_score, has_data)
        
        # Check exact match
        for table in self.actual_tables:
            if table.lower() == query_lower:
                has_data = not self.table_is_empty.get(table, False)
                candidates.append((table, 100, has_data))
        
        # Use fuzzy matching
        for table in self.actual_tables:
            scores = [
                fuzz.ratio(query_lower, table.lower()),
                fuzz.partial_ratio(query_lower, table.lower()),
            ]
            
            # Boost score for substring matches
            if query_lower in table.lower() or table.lower() in query_lower:
                scores.append(85)
            
            max_score = max(scores)
            if max_score >= 60:  # threshold
                has_data = not self.table_is_empty.get(table, False)
                candidates.append((table, max_score, has_data))
        
        if not candidates:
            return None
        
        # Sort candidates by:
        # 1. Prefer tables with data (has_data = True)
        # 2. Higher score
        # 3. Shorter name (likely base table)
        candidates.sort(key=lambda x: (x[2], x[1], -len(x[0])), reverse=True)
        
        best_candidate = candidates[0]
        best_table = best_candidate[0]
        base_score = best_candidate[1]
        has_data = best_candidate[2]
        
        # Log when we choose a table with data over an empty one
        if len(candidates) > 1:
            for other in candidates[1:]:
                if abs(other[1] - base_score) <= 10:  # Similar score
                    if has_data and not other[2]:
                        print(f"    → Chose '{best_table}' (with data) over '{other[0]}' (empty)")
        
        return (best_table, base_score)

def test_fuzzy_matcher():
    """Test the fuzzy matcher with empty and populated tables"""
    
    # Create a mock schema
    mock_schema = {
        "tables": {
            "city": {
                "row_count": 0,
                "is_empty": True,
            },
            "cities": {
                "row_count": 5,
                "is_empty": False,
            },
            "product": {
                "row_count": 0,
                "is_empty": True,
            },
            "products": {
                "row_count": 5,
                "is_empty": False,
            },
            "customer": {
                "row_count": 3,
                "is_empty": False,
            },
            "customers": {
                "row_count": 0,
                "is_empty": True,
            }
        }
    }
    
    # Initialize matcher
    matcher = SimpleFuzzyMatcher()
    matcher.learn_from_schema(mock_schema)
    
    print("Testing Fuzzy Matcher - Empty vs Populated Table Preference")
    print("=" * 70)
    print("\nDatabase tables:")
    for table_name, info in mock_schema["tables"].items():
        status = "EMPTY" if info["is_empty"] else f"POPULATED ({info['row_count']} rows)"
        print(f"  - {table_name}: {status}")
    
    print("\n" + "-" * 70)
    print("Testing fuzzy matching:\n")
    
    # Test cases
    test_cases = [
        ("city", "cities"),      # Should choose 'cities' (has data)
        ("product", "products"),  # Should choose 'products' (has data)
        ("customer", "customer"), # Should choose 'customer' (has data)
    ]
    
    all_passed = True
    
    for query, expected in test_cases:
        print(f"\nQuery: '{query}'")
        result = matcher.find_best_table_match(query)
        if result:
            matched_table, score = result
            is_empty = mock_schema["tables"][matched_table]["is_empty"]
            row_count = mock_schema["tables"][matched_table]["row_count"]
            status = "EMPTY" if is_empty else f"{row_count} rows"
            
            if matched_table == expected:
                print(f"  ✅ Matched: '{matched_table}' (score: {score}, {status})")
            else:
                print(f"  ❌ Matched: '{matched_table}' but expected: '{expected}'")
                all_passed = False
        else:
            print(f"  ❌ No match found (expected: '{expected}')")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ SUCCESS: Fuzzy matcher correctly prefers tables with data!")
        print("\nThis means:")
        print("  - When user queries 'city', we use 'cities' table (has 5 rows)")
        print("  - When user queries 'product', we use 'products' table (has 5 rows)")
        print("  - When user queries 'customer', we use 'customer' table (has 3 rows)")
    else:
        print("❌ FAILURE: Some tests failed.")
    
    return all_passed

if __name__ == "__main__":
    test_fuzzy_matcher()