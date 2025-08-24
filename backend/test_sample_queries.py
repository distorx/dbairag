#!/usr/bin/env python3
"""
Test a sample of queries to verify the system uses tables, indexes, relations, and enums.
"""

import json
import time
import requests
from typing import List, Dict, Any
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000/api"
CONNECTION_ID = 1

def get_sample_queries() -> List[str]:
    """Get a diverse sample of test queries"""
    return [
        # Basic counts
        "count students",
        "count applications", 
        "count cities",
        
        # Location queries with accents
        "count students from Bayamón",
        "students from San Juan",
        "applications from Mayagüez",
        
        # Status queries (using enums)
        "count students with rejected application",
        "count students with approved application",
        "show pending applications",
        
        # JOIN queries (relationships)
        "students with applications",
        "students without applications",
        "students with family members",
        "students with more than 2 family members",
        
        # Complex queries
        "students from Bayamón with rejected applications",
        "students from San Juan with documents",
        
        # Aggregation
        "count students by application status with total",
        "average family members per student",
        
        # Pattern matching
        "students whose name starts with A",
        "cities containing San",
        
        # Date queries
        "applications submitted this year",
        
        # Existence checks
        "are there any rejected applications",
        
        # Limit queries
        "show first 10 students",
        "top 5 applications"
    ]


def test_query(prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """Test a single query and return results"""
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/queries/execute",
            json={
                "connection_id": CONNECTION_ID,
                "prompt": prompt
            },
            timeout=timeout
        )
        execution_time = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            result = response.json()
            generated_sql = result.get("generated_sql", "")
            
            # Analyze SQL features
            features = []
            if "WITH (INDEX" in generated_sql:
                features.append("INDEX")
            if "JOIN" in generated_sql:
                features.append("JOIN")
            if "WHERE" in generated_sql:
                features.append("WHERE")
            if "GROUP BY" in generated_sql:
                features.append("GROUP")
            if "Status =" in generated_sql or "Status IN" in generated_sql:
                features.append("ENUM")
            if "COLLATE" in generated_sql:
                features.append("COLLATE")
            if "NOLOCK" in generated_sql:
                features.append("NOLOCK")
            if "COUNT" in generated_sql:
                features.append("AGGREGATE")
            if "AVG" in generated_sql or "SUM" in generated_sql:
                features.append("AGGREGATE")
            
            # Determine which tables are used
            tables_used = []
            if "Students" in generated_sql:
                tables_used.append("Students")
            if "ScholarshipApplications" in generated_sql:
                tables_used.append("Applications")
            if "Cities" in generated_sql:
                tables_used.append("Cities")
            if "FamilyMembers" in generated_sql:
                tables_used.append("FamilyMembers")
            if "Documents" in generated_sql:
                tables_used.append("Documents")
            
            return {
                "prompt": prompt,
                "status": "success",
                "execution_time": execution_time,
                "generated_sql": generated_sql,
                "features": features,
                "tables": tables_used,
                "result_type": result.get("result_type"),
                "row_count": len(result.get("result_data", {}).get("data", [])) if isinstance(result.get("result_data"), dict) else 0
            }
        else:
            return {
                "prompt": prompt,
                "status": "error",
                "execution_time": execution_time,
                "error": f"HTTP {response.status_code}",
                "details": response.text[:200]
            }
    except requests.Timeout:
        return {
            "prompt": prompt,
            "status": "timeout",
            "execution_time": timeout * 1000,
            "error": "Query timeout"
        }
    except Exception as e:
        return {
            "prompt": prompt,
            "status": "error",
            "execution_time": 0,
            "error": str(e)
        }


def print_query_result(result: Dict[str, Any]):
    """Print a formatted query result"""
    print(f"\n{'='*80}")
    print(f"📝 Query: {result['prompt']}")
    print(f"{'='*80}")
    
    if result["status"] == "success":
        print(f"✅ Status: SUCCESS")
        print(f"⏱️  Time: {result['execution_time']} ms")
        print(f"📊 Result Type: {result['result_type']}")
        print(f"📈 Row Count: {result['row_count']}")
        
        if result['features']:
            print(f"🔧 SQL Features: {', '.join(result['features'])}")
        
        if result['tables']:
            print(f"📋 Tables Used: {', '.join(result['tables'])}")
        
        print(f"\n🔍 Generated SQL:")
        # Format SQL for better readability
        sql = result['generated_sql']
        sql = sql.replace(' FROM ', '\nFROM ')
        sql = sql.replace(' WHERE ', '\nWHERE ')
        sql = sql.replace(' JOIN ', '\nJOIN ')
        sql = sql.replace(' GROUP BY ', '\nGROUP BY ')
        sql = sql.replace(' ORDER BY ', '\nORDER BY ')
        sql = sql.replace(' HAVING ', '\nHAVING ')
        print(f"  {sql}")
    else:
        print(f"❌ Status: {result['status'].upper()}")
        if 'error' in result:
            print(f"🚫 Error: {result['error']}")
        if 'details' in result:
            print(f"📋 Details: {result['details']}")


def main():
    """Main test execution"""
    print("=" * 80)
    print("RAG SQL Query System - Feature Usage Test")
    print("=" * 80)
    print(f"Testing: Tables, Indexes, Relations, Enums, and More")
    print(f"API Endpoint: {BASE_URL}")
    print("=" * 80)
    
    queries = get_sample_queries()
    print(f"\n📝 Testing {len(queries)} diverse queries...")
    
    results = []
    feature_count = {
        "INDEX": 0,
        "JOIN": 0,
        "WHERE": 0,
        "GROUP": 0,
        "ENUM": 0,
        "COLLATE": 0,
        "NOLOCK": 0,
        "AGGREGATE": 0
    }
    
    table_count = {
        "Students": 0,
        "Applications": 0,
        "Cities": 0,
        "FamilyMembers": 0,
        "Documents": 0
    }
    
    successful = 0
    errors = 0
    
    start_time = time.time()
    
    for query in queries:
        result = test_query(query)
        results.append(result)
        print_query_result(result)
        
        if result["status"] == "success":
            successful += 1
            for feature in result.get("features", []):
                if feature in feature_count:
                    feature_count[feature] += 1
            for table in result.get("tables", []):
                if table in table_count:
                    table_count[table] += 1
        else:
            errors += 1
    
    total_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    print(f"\n📊 Overall Results:")
    print(f"  Total Queries: {len(queries)}")
    print(f"  Successful: {successful} ({successful/len(queries)*100:.1f}%)")
    print(f"  Errors: {errors} ({errors/len(queries)*100:.1f}%)")
    print(f"  Total Time: {total_time:.1f} seconds")
    print(f"  Avg Time per Query: {total_time/len(queries)*1000:.0f} ms")
    
    print(f"\n🔧 SQL Feature Usage (out of {successful} successful queries):")
    for feature, count in sorted(feature_count.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / successful * 100) if successful > 0 else 0
            bar = "█" * int(percentage / 5)  # Visual bar (20 chars max)
            print(f"  {feature:<10} {count:>3} ({percentage:>5.1f}%) {bar}")
    
    print(f"\n📋 Table Usage (out of {successful} successful queries):")
    for table, count in sorted(table_count.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / successful * 100) if successful > 0 else 0
            bar = "█" * int(percentage / 5)  # Visual bar (20 chars max)
            print(f"  {table:<15} {count:>3} ({percentage:>5.1f}%) {bar}")
    
    # Analyze optimization opportunities
    print(f"\n💡 Optimization Insights:")
    
    # Check if indexes are being used
    if feature_count["INDEX"] == 0:
        print("  ⚠️  No queries used indexes - consider adding index hints")
    else:
        print(f"  ✅ {feature_count['INDEX']} queries used indexes")
    
    # Check if JOINs are optimized
    if feature_count["JOIN"] > 0:
        print(f"  ✅ {feature_count['JOIN']} queries used JOINs for relationships")
    
    # Check if enums are being utilized
    if feature_count["ENUM"] > 0:
        print(f"  ✅ {feature_count['ENUM']} queries utilized enum mappings")
    else:
        print("  ⚠️  No queries used enum mappings")
    
    # Check if COLLATE is used for accent-insensitive searches
    if feature_count["COLLATE"] > 0:
        print(f"  ✅ {feature_count['COLLATE']} queries used COLLATE for accent handling")
    else:
        print("  ⚠️  No queries used COLLATE - accent-sensitive searches may fail")
    
    # Check NOLOCK usage
    if feature_count["NOLOCK"] > 0:
        print(f"  ✅ {feature_count['NOLOCK']} queries used NOLOCK for read optimization")
    
    # Save results
    output_file = f"test_results_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "queries": results,
            "statistics": {
                "total": len(queries),
                "successful": successful,
                "errors": errors,
                "feature_usage": feature_count,
                "table_usage": table_count,
                "total_time": total_time
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()