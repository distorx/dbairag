#!/usr/bin/env python3
"""
Comprehensive test suite with 100 queries demonstrating all system capabilities.
Tests tables, indexes, relations (JOINs), enums, and optimization features.
"""

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import List, Dict, Tuple
import concurrent.futures

BASE_URL = "http://localhost:8000/api"

# 100 comprehensive test queries covering all features
test_queries = [
    # === BASIC TABLE QUERIES (1-10) ===
    ("count all students", "Basic count on Students table"),
    ("show all cities", "Select all from Cities table"),
    ("list scholarship applications", "Query ScholarshipApplications table"),
    ("count family members", "Count from FamilyMembers table"),
    ("show all documents", "Query Documents table"),
    ("list all students with id", "Students with primary key"),
    ("count distinct cities", "Distinct on Cities"),
    ("show student names", "Specific column selection"),
    ("count active students", "WHERE clause with IsActive"),
    ("list first 10 students", "LIMIT/TOP clause"),
    
    # === ENUM VALUE QUERIES (11-20) ===
    ("students with pending application", "Enum: pending = 1"),
    ("count submitted applications", "Enum: submitted = 2"),
    ("show applications under review", "Enum: under review = 3"),
    ("approved scholarship applications", "Enum: approved = 4"),
    ("rejected applications count", "Enum: rejected = 5"),
    ("cancelled application list", "Enum: cancelled = 6"),
    ("students with withdrawn applications", "Enum: withdrawn = 7"),
    ("applications not rejected", "Enum: Status != 5"),
    ("applications pending or submitted", "Enum: Status IN (1,2)"),
    ("non-cancelled applications", "Enum: Status != 6"),
    
    # === LOCATION QUERIES WITH ACCENTS (21-30) ===
    ("students from Bayamón", "COLLATE for city with accent"),
    ("count students in San Sebastián", "Spanish city name"),
    ("list students from Mayagüez", "City with umlaut"),
    ("students in Caguas", "Simple city name"),
    ("count from Ponce", "Another PR city"),
    ("students from San Juan", "Capital city query"),
    ("list from Arecibo", "Northern city"),
    ("count in Guaynabo", "Metro area city"),
    ("students from Río Grande", "City with accent"),
    ("list from Añasco", "City with ñ"),
    
    # === SIMPLE JOINS (31-40) ===
    ("students with applications", "INNER JOIN Students-Applications"),
    ("students without applications", "LEFT JOIN with NULL check"),
    ("students with family members", "JOIN Students-FamilyMembers"),
    ("students with documents", "JOIN Students-Documents"),
    ("applications with student names", "JOIN for display"),
    ("family members by student", "JOIN with aggregation"),
    ("documents per student", "JOIN with COUNT"),
    ("cities with students", "JOIN Cities-Students"),
    ("students with postal address", "JOIN on CityIdPostal"),
    ("students with physical address", "JOIN on CityIdPhysical"),
    
    # === COMPLEX MULTI-TABLE JOINS (41-50) ===
    ("students from Bayamón with rejected applications", "3-table JOIN with enum"),
    ("approved students from San Juan", "Location + Status JOIN"),
    ("students with family in same city", "Self-referential JOIN"),
    ("complete applications with all documents", "4-table JOIN"),
    ("pending applications from metro area", "Complex location JOIN"),
    ("students with more than 3 family members", "JOIN with HAVING"),
    ("rejected applications with incomplete documents", "Complex business logic"),
    ("approved students without family", "Multiple conditions"),
    ("students in Ponce with submitted applications", "Location + enum"),
    ("applications with documents from Mayagüez students", "4-way JOIN"),
    
    # === AGGREGATION QUERIES (51-60) ===
    ("average family members per student", "AVG aggregation"),
    ("total applications by status", "GROUP BY with enum"),
    ("count students by city", "GROUP BY location"),
    ("maximum documents per student", "MAX aggregation"),
    ("minimum family size", "MIN aggregation"),
    ("sum of all applications", "SUM aggregation"),
    ("students grouped by application status", "Complex GROUP BY"),
    ("cities ranked by student count", "ORDER BY with COUNT"),
    ("top 5 cities by applications", "GROUP BY with LIMIT"),
    ("status distribution percentages", "Calculated percentages"),
    
    # === PATTERN MATCHING (61-70) ===
    ("students whose name starts with A", "LIKE 'A%' pattern"),
    ("cities containing San", "LIKE '%San%' pattern"),
    ("students with email ending in .edu", "Email pattern match"),
    ("family members named Maria", "Name pattern"),
    ("documents with PDF in name", "Document pattern"),
    ("applications created in 2024", "Date pattern"),
    ("students with phone starting 787", "Phone pattern"),
    ("cities ending in 'bo'", "Suffix pattern"),
    ("students with middle name", "Complex name pattern"),
    ("applications with notes containing urgent", "Text search"),
    
    # === BUSINESS LOGIC QUERIES (71-80) ===
    ("students eligible for scholarship", "Complex eligibility rules"),
    ("incomplete applications needing documents", "Business validation"),
    ("students ready for interview", "Multi-condition check"),
    ("high priority applications", "Priority calculation"),
    ("at-risk students", "Risk assessment query"),
    ("graduation candidates", "Complex criteria"),
    ("students needing financial aid", "Financial logic"),
    ("applications missing signatures", "Document validation"),
    ("students with expired documents", "Date validation"),
    ("duplicate applications detection", "Data quality check"),
    
    # === PERFORMANCE OPTIMIZATION QUERIES (81-90) ===
    ("indexed search on student id", "Primary key optimization"),
    ("foreign key traversal optimization", "FK index usage"),
    ("covering index query", "Index-only scan"),
    ("filtered index usage", "Partial index"),
    ("sorted results using index", "Index ORDER BY"),
    ("distinct using unique index", "Unique constraint usage"),
    ("range scan on dates", "Date index scan"),
    ("hash join for large tables", "Join optimization"),
    ("nested loop for small tables", "Join strategy"),
    ("parallel query execution", "Parallelism hint"),
    
    # === EDGE CASES AND SPECIAL QUERIES (91-100) ===
    ("students with null values", "NULL handling"),
    ("applications with empty status", "Empty field check"),
    ("orphaned family members", "Referential integrity"),
    ("students with special characters in name", "Unicode handling"),
    ("case insensitive name search", "COLLATE for names"),
    ("students with multiple applications", "Duplicate handling"),
    ("timezone-aware date queries", "Date/time handling"),
    ("recursive family relationships", "CTE/recursive query"),
    ("pivot table of status by city", "PIVOT operation"),
    ("running total of applications", "Window function")
]

def execute_query(query_data: Tuple[str, str], connection_id: int = 1) -> Dict:
    """Execute a single query and return results with timing"""
    prompt, description = query_data
    
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/queries/execute",
            json={"connection_id": connection_id, "prompt": prompt},
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            sql = result.get("generated_sql", "")
            
            # Analyze SQL features used
            features = analyze_sql_features(sql)
            
            return {
                "prompt": prompt,
                "description": description,
                "success": True,
                "elapsed_ms": elapsed * 1000,
                "sql": sql,
                "features": features,
                "row_count": len(result.get("result_data", {}).get("data", [])),
                "optimization": result.get("metadata", {}).get("optimization", {})
            }
        else:
            return {
                "prompt": prompt,
                "description": description,
                "success": False,
                "elapsed_ms": elapsed * 1000,
                "error": f"HTTP {response.status_code}",
                "features": []
            }
    except Exception as e:
        return {
            "prompt": prompt,
            "description": description,
            "success": False,
            "elapsed_ms": 0,
            "error": str(e),
            "features": []
        }

def analyze_sql_features(sql: str) -> List[str]:
    """Analyze SQL to identify features used"""
    features = []
    sql_upper = sql.upper()
    
    # Check for various SQL features
    if "JOIN" in sql_upper:
        features.append("JOIN")
        if "INNER JOIN" in sql_upper:
            features.append("INNER_JOIN")
        if "LEFT JOIN" in sql_upper:
            features.append("LEFT_JOIN")
        if "RIGHT JOIN" in sql_upper:
            features.append("RIGHT_JOIN")
    
    if "WHERE" in sql_upper:
        features.append("WHERE")
    
    if "GROUP BY" in sql_upper:
        features.append("GROUP_BY")
    
    if "HAVING" in sql_upper:
        features.append("HAVING")
    
    if "ORDER BY" in sql_upper:
        features.append("ORDER_BY")
    
    if any(func in sql_upper for func in ["COUNT", "SUM", "AVG", "MAX", "MIN"]):
        features.append("AGGREGATE")
    
    if "DISTINCT" in sql_upper:
        features.append("DISTINCT")
    
    if "TOP" in sql_upper or "LIMIT" in sql_upper:
        features.append("LIMIT")
    
    if "COLLATE" in sql_upper:
        features.append("COLLATE")
    
    if "WITH (NOLOCK)" in sql_upper:
        features.append("NOLOCK")
    
    # Check for enum usage (Status = number)
    if "Status =" in sql or "Status IN" in sql:
        features.append("ENUM")
    
    # Check for index hints
    if "INDEX" in sql_upper or "FORCESEEK" in sql_upper:
        features.append("INDEX_HINT")
    
    # Count tables referenced
    tables = []
    for table in ["Students", "ScholarshipApplications", "Cities", "FamilyMembers", "Documents"]:
        if table in sql:
            tables.append(table)
    if len(tables) > 1:
        features.append(f"MULTI_TABLE_{len(tables)}")
    
    return features

def print_results(results: List[Dict]):
    """Print formatted test results"""
    print("\n" + "=" * 100)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 100)
    
    # Calculate statistics
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"\n✅ Success Rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    
    if successful:
        avg_time = sum(r["elapsed_ms"] for r in successful) / len(successful)
        min_time = min(r["elapsed_ms"] for r in successful)
        max_time = max(r["elapsed_ms"] for r in successful)
        
        print(f"\n⏱️  Performance Metrics:")
        print(f"  Average: {avg_time:.0f}ms")
        print(f"  Minimum: {min_time:.0f}ms")
        print(f"  Maximum: {max_time:.0f}ms")
    
    # Feature usage statistics
    all_features = {}
    for r in successful:
        for feature in r.get("features", []):
            all_features[feature] = all_features.get(feature, 0) + 1
    
    if all_features:
        print(f"\n🔧 SQL Features Used:")
        for feature, count in sorted(all_features.items(), key=lambda x: x[1], reverse=True):
            print(f"  {feature}: {count} queries ({count/len(successful)*100:.1f}%)")
    
    # Optimization statistics
    optimized = [r for r in successful if r.get("optimization", {}).get("optimizations")]
    if optimized:
        print(f"\n⚡ Query Optimization:")
        print(f"  Optimized: {len(optimized)} queries ({len(optimized)/len(successful)*100:.1f}%)")
        
        optimization_types = {}
        for r in optimized:
            for opt in r["optimization"].get("optimizations", []):
                optimization_types[opt] = optimization_types.get(opt, 0) + 1
        
        if optimization_types:
            print(f"  Optimization Types:")
            for opt_type, count in sorted(optimization_types.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {opt_type}: {count}")
    
    # Show failed queries
    if failed:
        print(f"\n❌ Failed Queries ({len(failed)}):")
        for r in failed[:10]:  # Show first 10 failures
            print(f"  - {r['prompt']}: {r.get('error', 'Unknown error')}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    # Show sample successful queries
    print(f"\n✨ Sample Successful Queries:")
    for r in successful[:5]:
        print(f"  - {r['prompt']} ({r['elapsed_ms']:.0f}ms)")
        if r.get("features"):
            print(f"    Features: {', '.join(r['features'])}")

def run_parallel_tests(queries: List[Tuple[str, str]], max_workers: int = 5) -> List[Dict]:
    """Run tests in parallel for better performance"""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all queries
        future_to_query = {executor.submit(execute_query, query): query for query in queries}
        
        # Process completed queries with progress indicator
        completed = 0
        for future in concurrent.futures.as_completed(future_to_query):
            result = future.result()
            results.append(result)
            completed += 1
            
            # Progress indicator
            if completed % 10 == 0:
                print(f"  Completed {completed}/{len(queries)} queries...")
    
    return results

def main():
    print("=" * 100)
    print("🚀 COMPREHENSIVE SYSTEM CAPABILITY TEST - 100 QUERIES")
    print("=" * 100)
    print(f"Testing: Tables, Indexes, Relations (JOINs), Enums, Optimizations")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    print(f"\n📝 Running {len(test_queries)} comprehensive test queries...")
    print("  Using parallel execution for better performance...")
    
    start_time = time.time()
    
    # Run tests in parallel
    results = run_parallel_tests(test_queries, max_workers=5)
    
    total_time = time.time() - start_time
    
    # Print results
    print_results(results)
    
    print(f"\n⏱️  Total Test Time: {total_time:.1f} seconds")
    print(f"  Average per query: {total_time/len(test_queries)*1000:.0f}ms")
    
    # Save detailed results to file
    with open("test_results_comprehensive_100.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(test_queries),
            "total_time_seconds": total_time,
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: test_results_comprehensive_100.json")
    
    print("\n" + "=" * 100)
    print("✅ COMPREHENSIVE TEST COMPLETE!")
    print("=" * 100)

if __name__ == "__main__":
    main()