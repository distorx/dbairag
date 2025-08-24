#!/usr/bin/env python3
"""
Test identification and SSN query patterns.
Shows how the system handles different identification-related queries.
"""

from datetime import datetime

def show_identification_patterns():
    """Display SQL patterns for identification-related queries"""
    
    print("=" * 100)
    print("🎯 IDENTIFICATION & SSN QUERY PATTERNS")
    print("=" * 100)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Demonstrating how the system handles IdentificationNumber vs SSN queries")
    print("=" * 100)
    
    patterns = [
        {
            "category": "📋 IDENTIFICATION NUMBER QUERIES",
            "description": "Uses the IdentificationNumber field for general ID numbers",
            "queries": [
                {
                    "prompt": "count students with identification number",
                    "sql": "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE IdentificationNumber IS NOT NULL AND IdentificationNumber != ''",
                    "purpose": "Students who have an ID number"
                },
                {
                    "prompt": "count students without identification number",
                    "sql": "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE IdentificationNumber IS NULL OR IdentificationNumber = ''",
                    "purpose": "Students missing ID number"
                },
                {
                    "prompt": "students with no identification",
                    "sql": "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE IdentificationNumber IS NULL OR IdentificationNumber = ''",
                    "purpose": "Alternative phrasing for missing ID"
                },
                {
                    "prompt": "list students with ID number",
                    "sql": "SELECT * FROM Students WITH (NOLOCK) WHERE IdentificationNumber IS NOT NULL AND IdentificationNumber != ''",
                    "purpose": "Show all students with IDs"
                }
            ]
        },
        {
            "category": "🔢 SOCIAL SECURITY NUMBER (SSN) QUERIES",
            "description": "Uses the SSN field specifically for Social Security Numbers",
            "queries": [
                {
                    "prompt": "count students with SSN",
                    "sql": "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE SSN IS NOT NULL AND SSN != ''",
                    "purpose": "Students who have SSN on file"
                },
                {
                    "prompt": "count students without SSN",
                    "sql": "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE SSN IS NULL OR SSN = ''",
                    "purpose": "Students missing SSN"
                },
                {
                    "prompt": "students with social security number",
                    "sql": "SELECT * FROM Students WITH (NOLOCK) WHERE SSN IS NOT NULL AND SSN != ''",
                    "purpose": "List students with SSN"
                },
                {
                    "prompt": "students without social security",
                    "sql": "SELECT * FROM Students WITH (NOLOCK) WHERE SSN IS NULL OR SSN = ''",
                    "purpose": "Students without SSN"
                }
            ]
        },
        {
            "category": "🔄 COMBINED QUERIES",
            "description": "Queries that could check both fields",
            "queries": [
                {
                    "prompt": "students with both ID and SSN",
                    "sql": "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE (IdentificationNumber IS NOT NULL AND IdentificationNumber != '') AND (SSN IS NOT NULL AND SSN != '')",
                    "purpose": "Students with complete identification"
                },
                {
                    "prompt": "students missing any identification",
                    "sql": "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE (IdentificationNumber IS NULL OR IdentificationNumber = '') OR (SSN IS NULL OR SSN = '')",
                    "purpose": "Students missing either ID or SSN"
                },
                {
                    "prompt": "students with complete identification info",
                    "sql": "SELECT * FROM Students WITH (NOLOCK) WHERE (IdentificationNumber IS NOT NULL AND IdentificationNumber != '') AND (SSN IS NOT NULL AND SSN != '')",
                    "purpose": "Fully identified students"
                }
            ]
        }
    ]
    
    for category_data in patterns:
        print(f"\n{category_data['category']}")
        print(f"📝 {category_data['description']}")
        print("-" * 80)
        
        for query in category_data['queries']:
            print(f"\n🔍 Query: \"{query['prompt']}\"")
            print(f"   Purpose: {query['purpose']}")
            print(f"   SQL:")
            
            # Format SQL for display
            sql_formatted = query['sql'].replace(' WHERE ', '\n     WHERE ').replace(' AND ', '\n       AND ').replace(' OR ', '\n       OR ')
            for line in sql_formatted.split('\n'):
                print(f"     {line}")
    
    print("\n" + "=" * 100)
    print("📊 KEY INSIGHTS")
    print("=" * 100)
    
    print("\n✅ Field Distinctions:")
    print("  • IdentificationNumber: General ID numbers (driver's license, passport, etc.)")
    print("  • SSN: Specifically Social Security Numbers")
    
    print("\n✅ Pattern Recognition:")
    print("  • 'identification', 'ID number', 'ident' → IdentificationNumber field")
    print("  • 'SSN', 'social security' → SSN field")
    
    print("\n✅ NULL Handling:")
    print("  • Checks both NULL and empty string ('')")
    print("  • 'with' queries use: IS NOT NULL AND != ''")
    print("  • 'without' queries use: IS NULL OR = ''")
    
    print("\n✅ Query Optimization:")
    print("  • All queries include WITH (NOLOCK) for read optimization")
    print("  • Simple WHERE clauses for index usage")
    print("  • No unnecessary JOINs for single-table queries")
    
    print("\n" + "=" * 100)
    print("✨ DEMONSTRATION COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    show_identification_patterns()