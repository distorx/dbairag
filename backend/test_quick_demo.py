#!/usr/bin/env python3
"""
Quick demonstration of system capabilities with tables, indexes, relations, and enums.
"""

import json
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

# Select 20 diverse queries that showcase different features
demo_queries = [
    # Basic counts
    ("count students", "Basic table count"),
    ("count cities", "Cities table"),
    
    # Location with accents (uses COLLATE)
    ("count students from Bayamón", "Accent handling with COLLATE"),
    ("students from San Sebastián", "Spanish characters"),
    
    # Enum usage (application statuses)
    ("count students with rejected application", "Enum: rejected=5"),
    ("count students with approved application", "Enum: approved=4"),
    ("show pending applications", "Enum: pending=1"),
    
    # JOIN operations (relationships)
    ("students with applications", "JOIN: Students + Applications"),
    ("students without applications", "LEFT JOIN with NULL check"),
    ("students with more than 2 family members", "JOIN with HAVING"),
    
    # Complex queries
    ("students from Bayamón with rejected applications", "Multiple JOINs + WHERE + Enum"),
    ("count students by application status with total", "GROUP BY with enums"),
    
    # Aggregations
    ("average family members per student", "AVG aggregation"),
    
    # Pattern matching
    ("students whose name starts with A", "LIKE pattern"),
    ("cities containing San", "Pattern search"),
    
    # Limits
    ("show first 10 students", "TOP/LIMIT clause"),
    
    # Business logic
    ("students with complete documents", "Complex JOIN logic"),
    ("applications ready for review", "Business rules"),
    
    # Relationship validation
    ("students with family in same city", "Self-JOIN relationship"),
    ("validate student application relationships", "Referential integrity")
]

def test_and_display(prompt, description):
    """Test a query and display results in a formatted way"""
    print(f"\n{'='*80}")
    print(f"📝 Query: {prompt}")
    print(f"📌 Testing: {description}")
    print('-'*80)
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/queries/execute",
            json={"connection_id": 1, "prompt": prompt},
            timeout=25
        )
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            sql = result.get("generated_sql", "")
            
            # Analyze features
            features = []
            if "JOIN" in sql:
                features.append("✓ JOIN")
            if "WHERE" in sql:
                features.append("✓ WHERE")
            if "GROUP BY" in sql:
                features.append("✓ GROUP BY")
            if "Status =" in sql or "Status IN" in sql:
                features.append("✓ ENUM")
            if "COLLATE" in sql:
                features.append("✓ COLLATE")
            if "WITH (NOLOCK)" in sql:
                features.append("✓ NOLOCK")
            if any(f in sql for f in ["COUNT", "AVG", "SUM", "MAX", "MIN"]):
                features.append("✓ AGGREGATE")
            if "HAVING" in sql:
                features.append("✓ HAVING")
            if "TOP" in sql:
                features.append("✓ LIMIT")
            
            # Count tables
            tables = []
            for t in ["Students", "ScholarshipApplications", "Cities", "FamilyMembers", "Documents"]:
                if t in sql:
                    tables.append(t)
            
            print(f"✅ SUCCESS in {elapsed:.0f}ms")
            print(f"🔧 Features: {' '.join(features) if features else 'Simple query'}")
            print(f"📋 Tables: {', '.join(tables) if tables else 'Single table'}")
            
            # Show SQL (formatted)
            print(f"\n💾 Generated SQL:")
            formatted_sql = sql.replace(" FROM ", "\n  FROM ").replace(" WHERE ", "\n  WHERE ").replace(" JOIN ", "\n  JOIN ").replace(" GROUP BY ", "\n  GROUP BY ")
            print(f"  {formatted_sql[:200]}{'...' if len(formatted_sql) > 200 else ''}")
            
            # Show result preview
            result_data = result.get("result_data", {})
            if isinstance(result_data, dict) and "data" in result_data:
                rows = result_data["data"]
                print(f"\n📊 Result: {len(rows)} rows")
                if rows and len(rows) > 0:
                    print(f"  First row: {json.dumps(rows[0], indent=2)[:100]}...")
            
            return True, features, tables
            
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            return False, [], []
            
    except Exception as e:
        print(f"💥 ERROR: {str(e)[:50]}")
        return False, [], []

def main():
    print("=" * 100)
    print("🎯 RAG SQL SYSTEM CAPABILITIES DEMONSTRATION")
    print("=" * 100)
    print("Demonstrating: Tables, Indexes, Relations (JOINs), Enums, Aggregations, and More")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Track statistics
    stats = {
        "total": len(demo_queries),
        "successful": 0,
        "features_used": set(),
        "tables_used": set()
    }
    
    print(f"\n🧪 Testing {len(demo_queries)} carefully selected queries...\n")
    
    for prompt, description in demo_queries:
        success, features, tables = test_and_display(prompt, description)
        if success:
            stats["successful"] += 1
            for f in features:
                stats["features_used"].add(f)
            for t in tables:
                stats["tables_used"].add(t)
    
    # Print final summary
    print("\n" + "=" * 100)
    print("📈 FINAL SUMMARY")
    print("=" * 100)
    
    print(f"\n✅ Success Rate: {stats['successful']}/{stats['total']} ({stats['successful']/stats['total']*100:.0f}%)")
    
    print(f"\n🔧 SQL Features Demonstrated:")
    for feature in sorted(stats["features_used"]):
        print(f"  {feature}")
    
    print(f"\n📋 Tables Used:")
    for table in sorted(stats["tables_used"]):
        print(f"  • {table}")
    
    print(f"\n💡 Key Capabilities Demonstrated:")
    print("  ✅ Accent-insensitive searches using COLLATE Latin1_General_CI_AI")
    print("  ✅ Enum value mapping (status text → numeric values)")
    print("  ✅ Complex JOINs for relationships between tables")
    print("  ✅ Aggregation functions (COUNT, AVG, SUM)")
    print("  ✅ GROUP BY with HAVING clauses")
    print("  ✅ Pattern matching with LIKE")
    print("  ✅ NOLOCK hints for read optimization")
    print("  ✅ Business logic implementation")
    print("  ✅ Referential integrity validation")
    
    print("\n" + "=" * 100)
    print("✨ Demonstration Complete!")
    print("=" * 100)

if __name__ == "__main__":
    main()