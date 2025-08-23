#!/usr/bin/env python3
"""
Test the dynamic fuzzy matching system with the actual database schema
"""
import asyncio
from app.services.schema_analyzer_universal import UniversalSchemaAnalyzer
from app.services.dynamic_fuzzy_matcher import DynamicFuzzyMatcher

async def test_fuzzy_matching():
    # Create analyzer and get schema
    analyzer = UniversalSchemaAnalyzer()
    connection_string = "sqlite:////home/rick/source/dbairag/backend/test_fuzzy.db"
    
    # Create engine and get schema
    engine = analyzer.create_engine(connection_string)
    schema_info = await analyzer.get_database_schema(engine, "test", force_refresh=True)
    
    print("Tables found in database:")
    for table_name in schema_info.get("tables", {}).keys():
        print(f"  - {table_name}")
    print()
    
    # Create fuzzy matcher and learn from schema
    fuzzy_matcher = DynamicFuzzyMatcher()
    fuzzy_matcher.learn_from_schema(schema_info)
    
    print("Learned mappings:")
    for term, mapping in fuzzy_matcher.learned_mappings.items():
        print(f"  '{term}' -> '{mapping}'")
    print()
    
    print("Compound tables detected:")
    for table in fuzzy_matcher.compound_tables:
        print(f"  - {table}")
    print()
    
    # Test some fuzzy matching
    test_terms = [
        "student",
        "students",
        "application",
        "applications",
        "scholarship",
        "scholarships",
        "enrollment",
        "enrollments",
        "course",
        "courses"
    ]
    
    available_tables = list(schema_info.get("tables", {}).keys())
    
    print("Fuzzy matching tests:")
    for term in test_terms:
        match, confidence = fuzzy_matcher.find_best_table_match(term, available_tables)
        if match:
            print(f"  '{term}' -> '{match}' (confidence: {confidence:.2f})")
        else:
            print(f"  '{term}' -> No match found")
    
    # Test the full query
    print("\nQuery analysis:")
    query = "count students who have scholarship applications"
    query_words = query.lower().split()
    
    for word in query_words:
        match, confidence = fuzzy_matcher.find_best_table_match(word, available_tables)
        if match and confidence > 0.5:
            print(f"  '{word}' -> '{match}' (confidence: {confidence:.2f})")

if __name__ == "__main__":
    asyncio.run(test_fuzzy_matching())