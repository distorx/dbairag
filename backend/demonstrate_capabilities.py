#!/usr/bin/env python3
"""
Demonstrate system capabilities by showing example queries and their optimized SQL.
This avoids slow API calls by using the pattern matching system directly.
"""

import json
import sys
import os
from datetime import datetime

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.optimized_rag_service import OptimizedRAGService
from app.services.query_optimizer_service import QueryOptimizerService

def demonstrate_pattern_matching():
    """Show how pattern matching generates SQL for various query types"""
    
    service = OptimizedRAGService()
    optimizer = QueryOptimizerService()
    
    # Mock schema info for demonstration
    schema_info = {
        "tables": {
            "Students": ["Id", "Name", "Email", "CityIdPhysical", "CityIdPostal", "IsActive"],
            "ScholarshipApplications": ["Id", "StudentId", "Status", "CreatedDate"],
            "Cities": ["Id", "Name", "State"],
            "FamilyMembers": ["Id", "StudentId", "Name", "Relationship"],
            "Documents": ["Id", "StudentId", "DocumentType", "FileName"]
        },
        "indexes": {
            "Students": ["PK_Students(Id)", "IX_Students_CityIdPhysical", "IX_Students_CityIdPostal"],
            "ScholarshipApplications": ["PK_Applications(Id)", "IX_Applications_StudentId", "IX_Applications_Status"],
            "Cities": ["PK_Cities(Id)", "IX_Cities_Name"],
            "FamilyMembers": ["PK_FamilyMembers(Id)", "IX_FamilyMembers_StudentId"],
            "Documents": ["PK_Documents(Id)", "IX_Documents_StudentId"]
        },
        "foreign_keys": {
            "ScholarshipApplications": [("StudentId", "Students", "Id")],
            "Students": [("CityIdPhysical", "Cities", "Id"), ("CityIdPostal", "Cities", "Id")],
            "FamilyMembers": [("StudentId", "Students", "Id")],
            "Documents": [("StudentId", "Students", "Id")]
        },
        "table_stats": {
            "Students": {"row_count": 305},
            "ScholarshipApplications": {"row_count": 450},
            "Cities": {"row_count": 78},
            "FamilyMembers": {"row_count": 892},
            "Documents": {"row_count": 1247}
        }
    }
    
    # Test queries demonstrating all features
    test_cases = [
        {
            "category": "🏗️ BASIC TABLE ACCESS",
            "queries": [
                ("count students", "Simple COUNT on primary table"),
                ("show all cities", "SELECT * with index hints"),
                ("list first 10 students", "TOP/LIMIT with optimization")
            ]
        },
        {
            "category": "🔢 ENUM VALUE MAPPING",
            "queries": [
                ("students with rejected application", "Maps 'rejected' to Status = 5"),
                ("approved applications", "Maps 'approved' to Status = 4"),
                ("pending or submitted applications", "Maps to Status IN (1, 2)")
            ]
        },
        {
            "category": "🌍 LOCATION WITH ACCENTS (COLLATE)",
            "queries": [
                ("students from Bayamón", "Uses COLLATE Latin1_General_CI_AI"),
                ("count students in San Sebastián", "Handles Spanish characters"),
                ("list from Mayagüez", "Accent-insensitive search")
            ]
        },
        {
            "category": "🔗 RELATIONS (JOINs)",
            "queries": [
                ("students with applications", "INNER JOIN via foreign key"),
                ("students without applications", "LEFT JOIN with NULL check"),
                ("students with family members", "Multiple table relationships")
            ]
        },
        {
            "category": "📊 AGGREGATIONS",
            "queries": [
                ("average family members per student", "AVG with JOIN"),
                ("count students by application status", "GROUP BY with enum"),
                ("top 5 cities by student count", "Complex aggregation")
            ]
        },
        {
            "category": "⚡ OPTIMIZATION FEATURES",
            "queries": [
                ("indexed student search", "Uses primary key index"),
                ("foreign key traversal", "Optimizes JOIN order"),
                ("large result set query", "Applies parallel hints")
            ]
        }
    ]
    
    print("=" * 100)
    print("🎯 RAG SQL SYSTEM CAPABILITIES DEMONSTRATION")
    print("=" * 100)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Showing how the system uses: Tables, Indexes, Relations, Enums, and Optimizations")
    print("=" * 100)
    
    for test_group in test_cases:
        print(f"\n{test_group['category']}")
        print("-" * 80)
        
        for prompt, description in test_group['queries']:
            print(f"\n📝 Query: '{prompt}'")
            print(f"   Purpose: {description}")
            
            # Generate SQL using pattern matching
            sql = service._pattern_match_sql(prompt, schema_info, connection_id=1)
            
            if sql:
                # Apply optimization
                optimized_sql, optimization_metadata = optimizer.optimize_query(
                    sql, 
                    schema_info,
                    query_stats=None
                )
                
                if optimized_sql:
                    sql = optimized_sql
                    optimizations = optimization_metadata.get("optimizations", [])
                else:
                    optimizations = []
                
                # Format SQL for display
                formatted_sql = sql.replace(" FROM ", "\n     FROM ").replace(" WHERE ", "\n     WHERE ").replace(" JOIN ", "\n     JOIN ")
                
                print(f"   💾 Generated SQL:")
                for line in formatted_sql.split('\n'):
                    print(f"      {line}")
                
                # Show features used
                features = []
                sql_upper = sql.upper()
                
                if "JOIN" in sql_upper:
                    features.append("JOIN")
                if "WHERE" in sql_upper:
                    features.append("WHERE")
                if "Status =" in sql or "Status IN" in sql:
                    features.append("ENUM")
                if "COLLATE" in sql_upper:
                    features.append("COLLATE")
                if "WITH (NOLOCK)" in sql_upper:
                    features.append("NOLOCK")
                if "GROUP BY" in sql_upper:
                    features.append("GROUP BY")
                if any(f in sql_upper for f in ["COUNT", "AVG", "SUM"]):
                    features.append("AGGREGATE")
                
                if features:
                    print(f"   🔧 Features: {', '.join(features)}")
                
                if optimizations:
                    print(f"   ⚡ Optimizations: {', '.join(optimizations[:3])}")
            else:
                print(f"   ⚠️  Pattern not found (would use LLM)")
    
    # Summary of capabilities
    print("\n" + "=" * 100)
    print("📈 SYSTEM CAPABILITIES SUMMARY")
    print("=" * 100)
    
    print("\n✅ Table Management:")
    print("  • Direct table access with schema awareness")
    print("  • Multi-table queries with proper relationships")
    print("  • Table statistics for optimization decisions")
    
    print("\n✅ Index Usage:")
    print("  • Primary key optimization")
    print("  • Foreign key index traversal")
    print("  • NOLOCK hints for read optimization")
    print("  • Index-based sorting and filtering")
    
    print("\n✅ Relations (Foreign Keys):")
    print("  • Automatic JOIN generation from foreign keys")
    print("  • Optimized JOIN ordering based on statistics")
    print("  • Complex multi-table relationships")
    print("  • Self-referential relationships")
    
    print("\n✅ Enum Value Mapping:")
    print("  • Text to numeric conversion")
    print("  • Status mappings (pending=1, submitted=2, etc.)")
    print("  • IN clause for multiple enum values")
    print("  • Negative enum conditions (!=)")
    
    print("\n✅ Special Features:")
    print("  • COLLATE for accent-insensitive searches")
    print("  • Pattern matching with LIKE")
    print("  • Aggregation functions")
    print("  • Business logic implementation")
    
    print("\n✅ Query Optimization:")
    print("  • JOIN order optimization")
    print("  • Index hint generation")
    print("  • Predicate optimization")
    print("  • Missing index suggestions")
    print("  • Execution plan analysis")
    
    print("\n" + "=" * 100)
    print("💡 DEMONSTRATION COMPLETE")
    print("=" * 100)
    print("\nNote: This demonstration uses pattern matching to avoid slow API calls.")
    print("In production, queries not matching patterns would use OpenAI for generation.")
    print("All generated queries are automatically optimized using the QueryOptimizerService.")

if __name__ == "__main__":
    demonstrate_pattern_matching()