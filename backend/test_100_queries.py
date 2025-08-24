#!/usr/bin/env python3
"""
Test 100 diverse queries to demonstrate system capabilities with tables, indexes, relations, and enums.
"""

import json
import time
import requests
from typing import List, Dict, Any
from datetime import datetime
import concurrent.futures
import sys

# API Configuration
BASE_URL = "http://localhost:8000/api"
CONNECTION_ID = 1

def generate_100_queries() -> List[str]:
    """Generate 100 diverse test queries"""
    queries = [
        # 1-10: Basic counts
        "count students",
        "count applications",
        "count cities",
        "count family members",
        "count documents",
        "total students",
        "how many applications",
        "number of cities",
        "show count of documents",
        "total family members",
        
        # 11-20: Location queries with accents
        "count students from Bayamón",
        "students from San Juan",
        "applications from Mayagüez",
        "students from Ponce",
        "count students from Carolina",
        "students living in Caguas",
        "applications from Arecibo",
        "show students from Guaynabo",
        "students from San Sebastián",
        "count students from Río Grande",
        
        # 21-30: Status queries (using enums)
        "count students with rejected application",
        "count students with approved application",
        "show pending applications",
        "students with submitted applications",
        "applications under review",
        "cancelled applications",
        "count rejected applications",
        "show approved applications",
        "list pending scholarship applications",
        "total cancelled applications",
        
        # 31-40: JOIN operations (relationships)
        "students with applications",
        "students without applications",
        "students with family members",
        "students without family members",
        "students with documents",
        "students without documents",
        "students with more than 2 family members",
        "students with less than 3 family members",
        "students with exactly 1 family member",
        "applications with documents",
        
        # 41-50: Complex filtering
        "students from Bayamón with rejected applications",
        "students from San Juan with approved applications",
        "pending applications from Ponce",
        "students from Carolina with documents",
        "rejected applications from students with family",
        "approved applications with complete documents",
        "students from Mayagüez without applications",
        "students with birth certificate",
        "students without academic transcript",
        "applications missing documents",
        
        # 51-60: Aggregations
        "average family members per student",
        "count students by city",
        "count applications by status",
        "total documents per student",
        "students grouped by city",
        "applications grouped by status",
        "count students per application status",
        "distribution of application statuses",
        "most common city",
        "least common status",
        
        # 61-70: Pattern matching
        "students whose name starts with A",
        "students whose name contains Maria",
        "cities starting with San",
        "cities containing Bay",
        "students with gmail email",
        "applications with urgent in notes",
        "students with 787 phone",
        "addresses containing Calle",
        "names with accents",
        "students with Jr in name",
        
        # 71-80: Date/time queries
        "applications submitted today",
        "applications submitted this week",
        "applications submitted this month",
        "applications submitted this year",
        "recent applications",
        "old applications",
        "applications submitted in January",
        "morning submissions",
        "applications before deadline",
        "late submissions",
        
        # 81-90: Comparisons and rankings
        "students with most family members",
        "city with most applications",
        "top 5 students",
        "first 10 applications",
        "show 5 recent applications",
        "latest submitted application",
        "oldest application",
        "highest application count by city",
        "compare approved vs rejected",
        "busiest submission month",
        
        # 91-100: Business logic queries
        "eligible students for scholarship",
        "students meeting requirements",
        "applications ready for review",
        "high priority applications",
        "complete applications",
        "incomplete applications",
        "students with all documents",
        "verify pending applications exist",
        "check rejected applications count",
        "validate student application relationships"
    ]
    
    return queries


def test_query(prompt: str, timeout: int = 20) -> Dict[str, Any]:
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
            if "WITH (NOLOCK)" in generated_sql:
                features.append("NOLOCK")
            if any(func in generated_sql for func in ["COUNT", "AVG", "SUM", "MAX", "MIN"]):
                features.append("AGGREGATE")
            if "HAVING" in generated_sql:
                features.append("HAVING")
            if "ORDER BY" in generated_sql:
                features.append("ORDER")
            if "TOP" in generated_sql or "LIMIT" in generated_sql:
                features.append("LIMIT")
            
            # Determine which tables are used
            tables_used = []
            table_names = [
                "Students", "ScholarshipApplications", "Cities", 
                "FamilyMembers", "Documents", "StudentDocuments",
                "States", "Schools", "Addresses"
            ]
            for table in table_names:
                if table in generated_sql:
                    tables_used.append(table)
            
            # Get result data
            result_data = result.get("result_data", {})
            if isinstance(result_data, dict) and "data" in result_data:
                row_count = len(result_data["data"])
                first_row = result_data["data"][0] if result_data["data"] else None
            else:
                row_count = 0
                first_row = result_data
            
            return {
                "prompt": prompt[:50],  # Truncate for display
                "status": "✅",
                "time_ms": execution_time,
                "features": ", ".join(features) if features else "SIMPLE",
                "tables": len(tables_used),
                "rows": row_count,
                "sql_preview": generated_sql[:80] + "..." if len(generated_sql) > 80 else generated_sql
            }
        else:
            return {
                "prompt": prompt[:50],
                "status": "❌",
                "time_ms": execution_time,
                "error": f"HTTP {response.status_code}"
            }
    except requests.Timeout:
        return {
            "prompt": prompt[:50],
            "status": "⏱️",
            "time_ms": timeout * 1000,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "prompt": prompt[:50],
            "status": "💥",
            "time_ms": 0,
            "error": str(e)[:30]
        }


def test_queries_parallel(queries: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
    """Test queries in parallel for better performance"""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_query = {executor.submit(test_query, query): query for query in queries}
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_query):
            result = future.result()
            results.append(result)
            completed += 1
            
            # Progress indicator
            if completed % 10 == 0:
                print(f"  Progress: {completed}/100 ({completed}%)")
                sys.stdout.flush()
    
    return results


def main():
    """Main test execution"""
    print("=" * 100)
    print("🚀 RAG SQL SYSTEM - 100 QUERY COMPREHENSIVE TEST")
    print("=" * 100)
    print(f"Testing: Tables, Indexes, Relations, Enums, Aggregations, and More")
    print(f"Endpoint: {BASE_URL}/queries/execute")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Generate queries
    print("\n📝 Generating 100 test queries...")
    queries = generate_100_queries()
    
    # Test queries
    print(f"🧪 Testing {len(queries)} queries (parallel execution)...")
    start_time = time.time()
    
    results = test_queries_parallel(queries, max_workers=3)
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = sum(1 for r in results if r["status"] == "✅")
    errors = sum(1 for r in results if r["status"] == "❌")
    timeouts = sum(1 for r in results if r["status"] == "⏱️")
    crashes = sum(1 for r in results if r["status"] == "💥")
    
    # Feature analysis
    feature_stats = {}
    table_stats = {}
    time_stats = []
    
    for r in results:
        if r["status"] == "✅":
            # Track features
            if "features" in r:
                for feature in r["features"].split(", "):
                    feature_stats[feature] = feature_stats.get(feature, 0) + 1
            
            # Track tables
            if "tables" in r:
                table_count = r["tables"]
                if table_count > 0:
                    table_stats[f"{table_count} tables"] = table_stats.get(f"{table_count} tables", 0) + 1
            
            # Track times
            if "time_ms" in r:
                time_stats.append(r["time_ms"])
    
    # Print results table
    print("\n" + "=" * 100)
    print("📊 QUERY RESULTS")
    print("=" * 100)
    
    print("\n| # | Status | Time(ms) | Features | Tables | Rows | Query |")
    print("|---|--------|----------|----------|--------|------|-------|")
    
    for i, r in enumerate(results[:50], 1):  # Show first 50
        if r["status"] == "✅":
            print(f"| {i:2} | {r['status']} | {r['time_ms']:8} | {r.get('features', 'N/A')[:20]:20} | {r.get('tables', 0):6} | {r.get('rows', 0):4} | {r['prompt'][:40]} |")
        else:
            print(f"| {i:2} | {r['status']} | {r.get('time_ms', 0):8} | ERROR | - | - | {r['prompt'][:40]} |")
    
    if len(results) > 50:
        print(f"\n... and {len(results) - 50} more queries ...")
    
    # Print summary statistics
    print("\n" + "=" * 100)
    print("📈 SUMMARY STATISTICS")
    print("=" * 100)
    
    print(f"\n🎯 Success Rate:")
    print(f"  ✅ Successful: {successful}/{len(queries)} ({successful/len(queries)*100:.1f}%)")
    print(f"  ❌ Errors: {errors}/{len(queries)} ({errors/len(queries)*100:.1f}%)")
    print(f"  ⏱️ Timeouts: {timeouts}/{len(queries)} ({timeouts/len(queries)*100:.1f}%)")
    print(f"  💥 Crashes: {crashes}/{len(queries)} ({crashes/len(queries)*100:.1f}%)")
    
    print(f"\n⚡ Performance:")
    print(f"  Total Time: {total_time:.1f} seconds")
    print(f"  Queries/Second: {len(queries)/total_time:.1f}")
    if time_stats:
        print(f"  Avg Response: {sum(time_stats)/len(time_stats):.0f} ms")
        print(f"  Min Response: {min(time_stats)} ms")
        print(f"  Max Response: {max(time_stats)} ms")
        print(f"  Median Response: {sorted(time_stats)[len(time_stats)//2]} ms")
    
    print(f"\n🔧 SQL Feature Usage (from {successful} successful queries):")
    for feature, count in sorted(feature_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / successful * 100) if successful > 0 else 0
        bar = "█" * int(percentage / 2)  # Visual bar
        print(f"  {feature:12} : {count:3} ({percentage:5.1f}%) {bar}")
    
    print(f"\n📋 Table Complexity:")
    for complexity, count in sorted(table_stats.items(), key=lambda x: x[0]):
        percentage = (count / successful * 100) if successful > 0 else 0
        print(f"  {complexity:12} : {count:3} queries ({percentage:.1f}%)")
    
    # Identify interesting patterns
    print(f"\n💡 Key Insights:")
    
    if "JOIN" in feature_stats:
        print(f"  • {feature_stats['JOIN']} queries used JOINs for relationships")
    
    if "ENUM" in feature_stats:
        print(f"  • {feature_stats['ENUM']} queries utilized enum mappings for status values")
    
    if "COLLATE" in feature_stats:
        print(f"  • {feature_stats['COLLATE']} queries handled accents with COLLATE")
    
    if "AGGREGATE" in feature_stats:
        print(f"  • {feature_stats['AGGREGATE']} queries performed aggregations")
    
    if "GROUP" in feature_stats:
        print(f"  • {feature_stats['GROUP']} queries used GROUP BY for analysis")
    
    if "NOLOCK" in feature_stats:
        print(f"  • {feature_stats['NOLOCK']} queries optimized with NOLOCK hints")
    
    # Save results
    output_file = f"test_100_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "summary": {
                "total": len(queries),
                "successful": successful,
                "errors": errors,
                "timeouts": timeouts,
                "total_time": total_time,
                "queries_per_second": len(queries)/total_time
            },
            "features": feature_stats,
            "tables": table_stats,
            "queries": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print("\n" + "=" * 100)
    print("✨ Test completed successfully!")
    print("=" * 100)


if __name__ == "__main__":
    main()