#!/usr/bin/env python3
"""
Simple test to demonstrate the Database Vocabulary Service working
"""

from app.services.database_vocabulary_service import get_vocabulary_service
from app.services.optimized_rag_service import OptimizedRAGService

def test_vocabulary_patterns():
    """Test vocabulary-based pattern matching"""
    
    print("=" * 80)
    print("🎯 TESTING DATABASE VOCABULARY PATTERNS")
    print("=" * 80)
    
    # Initialize services
    vocab_service = get_vocabulary_service()
    rag_service = OptimizedRAGService()
    
    # Test queries
    test_queries = [
        "count students with identification number",
        "count students without mobile phone",
        "students with social security number",
        "applications with status rejected",
        "students from Bayamón",
        "documents of type transcript",
        "students with date of birth",
        "students with college board score",
        "family members with relationship mother",
        "students with driver's license"
    ]
    
    print("\n📚 Vocabulary Service Column Mapping:")
    print("-" * 80)
    
    # Show vocabulary mappings
    mappings = [
        ("identification number", "IdentificationNumber"),
        ("mobile phone", "MobilePhone"),
        ("social security number", "SSN"),
        ("date of birth", "DateOfBirth"),
        ("driver's license", "DriversLicense"),
        ("college board score", "CollegeBoardScore")
    ]
    
    for phrase, expected in mappings:
        actual = vocab_service.find_column_by_natural_language(phrase)
        status = "✅" if actual == expected else "❌"
        print(f"{status} '{phrase}' → {actual} (expected: {expected})")
    
    print("\n🔢 Enum Value Mapping:")
    print("-" * 80)
    
    # Test enum mappings
    enum_tests = [
        ("Status", "rejected", 5),
        ("Status", "approved", 4),
        ("Status", "pending", 1),
        ("DocumentType", "transcript", 1),
        ("Relationship", "mother", 1)
    ]
    
    for field, text, expected in enum_tests:
        actual = vocab_service.get_enum_value(field, text)
        status = "✅" if actual == expected else "❌"
        print(f"{status} {field} '{text}' → {actual} (expected: {expected})")
    
    print("\n📍 Location Detection:")
    print("-" * 80)
    
    # Test location detection
    locations = [
        ("Bayamón", True, "city"),
        ("San Juan", True, "city"),
        ("Puerto Rico", True, "state"),
        ("Metro", True, "region"),
        ("InvalidCity", False, "")
    ]
    
    for location, expected_found, expected_type in locations:
        found, loc_type = vocab_service.is_location(location)
        status = "✅" if found == expected_found and loc_type == expected_type else "❌"
        print(f"{status} '{location}' → {loc_type if found else 'not found'} (expected: {expected_type if expected_found else 'not found'})")
    
    print("\n🔍 SQL Pattern Generation:")
    print("-" * 80)
    
    # Test SQL generation using vocabulary
    for query in test_queries[:5]:
        print(f"\nQuery: '{query}'")
        
        # Generate SQL using vocabulary
        sql = rag_service._generate_vocabulary_based_query(query.lower(), query)
        
        if sql:
            print(f"✅ Generated SQL:")
            # Clean up SQL for display
            sql_display = sql.replace("  ", " ").strip()
            if len(sql_display) > 150:
                sql_display = sql_display[:150] + "..."
            print(f"   {sql_display}")
        else:
            print(f"❌ No pattern matched")
    
    print("\n" + "=" * 80)
    print("✨ VOCABULARY PATTERN TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_vocabulary_patterns()