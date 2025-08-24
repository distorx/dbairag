#!/usr/bin/env python3
"""
Comprehensive test with 200 bizarre and challenging queries
to test the enhanced SQL generation system with full metadata
"""

import requests
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import random

# API endpoint
API_URL = "http://localhost:8001/api/queries/execute-optimized"

def generate_bizarre_queries() -> List[Dict[str, str]]:
    """Generate 200 diverse and challenging queries"""
    queries = []
    
    # Basic counting queries with variations (20)
    basic_counts = [
        "count all the students please",
        "how many cities exist?",
        "total number of family members",
        "count regions in database",
        "number of high schools",
        "count municipios",
        "total occupations available",
        "how many scholarship applications",
        "count student profiles",
        "number of student documents",
        "total questions in system",
        "count all answers",
        "how many users in aspnet",
        "total roles defined",
        "count audit logs",
        "number of document submissions",
        "count student dependents",
        "how many family members total",
        "count inactive students",
        "total deleted records"
    ]
    
    # Complex relationship queries (30)
    relationship_queries = [
        "show me students who have family members",
        "which students have no family",
        "students with more than 3 family members",
        "students with exactly 2 dependents",
        "show family members who are deceased",
        "active students with approved applications",
        "students from San Juan city",
        "family members who are legal representatives",
        "students with scholarships in draft status",
        "show all orphaned students",
        "married students with children",
        "single students without dependents",
        "students with both parents",
        "family members over 65 years old",
        "students under 18 with guardians",
        "show twins in the system",
        "students with same last name as family",
        "international students",
        "local students from current city",
        "transferred students",
        "graduated students with honors",
        "students who dropped out",
        "readmitted students",
        "students on academic probation",
        "honor roll students",
        "students with perfect attendance",
        "part-time vs full-time students",
        "students enrolled in summer",
        "gap year students",
        "students with incomplete applications"
    ]
    
    # Aggregation and grouping queries (25)
    aggregation_queries = [
        "average age of students",
        "count students by city",
        "group family members by relationship type",
        "students per high school",
        "applications by status with totals",
        "monthly application submissions",
        "yearly enrollment trends",
        "students grouped by age ranges",
        "family size distribution",
        "most common first names",
        "most common last names",
        "popular cities for students",
        "least populated regions",
        "occupations by frequency",
        "average family income",
        "scholarship amounts by status",
        "rejection rate by month",
        "approval rate by region",
        "demographic breakdown by city",
        "gender distribution",
        "age pyramid of students",
        "family members per student average",
        "documents per student average",
        "completion rate of applications",
        "time to approval statistics"
    ]
    
    # Bizarre and unusual queries (40)
    bizarre_specific = [
        "find zombie students",
        "show me time travelers",
        "students born on leap year",
        "friday the 13th applications",
        "palindrome student ids",
        "students with no vowels in name",
        "longest student name",
        "shortest email address",
        "students with numbers in names",
        "special character emails",
        "duplicate entries detection",
        "ghost records with null everything",
        "future dated applications",
        "backdated submissions",
        "negative age students",
        "centenarian family members",
        "unborn applicants",
        "applications from the past",
        "weekend only submissions",
        "midnight applications",
        "3am system usage",
        "full moon submissions",
        "mercury retrograde applications",
        "lucky number 7 in ids",
        "unlucky 13 in records",
        "sequential id patterns",
        "fibonacci sequence in data",
        "prime number student ids",
        "perfect square record counts",
        "golden ratio in statistics",
        "pi appearances in data",
        "binary pattern ids",
        "hexadecimal references",
        "morse code in names",
        "emoji in text fields",
        "sql injection attempts in names",
        "xss attempts in applications",
        "buffer overflow test names",
        "unicode chaos test",
        "null byte injection tests"
    ]
    
    # Complex JOIN queries (25)
    join_queries = [
        "students with their cities and regions",
        "family members with occupations and students",
        "complete student profile with all relations",
        "applications with student and family details",
        "multi-generational family trees",
        "students sharing same address",
        "siblings in the system",
        "parent-child relationships",
        "guardian assignments",
        "emergency contacts for students",
        "students with multiple applications",
        "reapplication patterns",
        "family members in multiple roles",
        "students as family members of others",
        "circular family references",
        "students from same high school",
        "alumni relationships",
        "referral networks",
        "students with same counselor",
        "batch application groups",
        "cohort analysis joins",
        "cross-referenced documents",
        "linked submissions",
        "related audit entries",
        "connected user sessions"
    ]
    
    # Date and time based queries (20)
    datetime_queries = [
        "applications submitted today",
        "students born this month",
        "family members birthday this week",
        "upcoming application deadlines",
        "expired documents",
        "recent audit logs",
        "last 24 hours activity",
        "weekend vs weekday submissions",
        "business hours applications",
        "after hours submissions",
        "holiday period applications",
        "summer vacation enrollments",
        "fiscal year summaries",
        "quarter-over-quarter growth",
        "year-over-year comparisons",
        "seasonal patterns",
        "monthly trends",
        "weekly cycles",
        "daily peaks",
        "hourly distribution"
    ]
    
    # Status and state queries (20)
    status_queries = [
        "pending approval applications",
        "rejected with reasons",
        "cancelled applications this month",
        "draft applications older than 30 days",
        "stale submissions",
        "abandoned applications",
        "incomplete profiles",
        "missing documents",
        "verification pending",
        "awaiting review",
        "escalated cases",
        "priority applications",
        "fast-tracked approvals",
        "delayed processing",
        "stuck in pipeline",
        "error state records",
        "corrupted data detection",
        "inconsistent status",
        "invalid state transitions",
        "rollback candidates"
    ]
    
    # Performance and edge case queries (20)
    performance_queries = [
        "largest family in system",
        "smallest complete application",
        "fastest approval time",
        "slowest processing case",
        "most documents submitted",
        "least active user",
        "most active day",
        "quietest period",
        "peak usage time",
        "system stress points",
        "bottleneck detection",
        "outlier identification",
        "anomaly detection",
        "unusual patterns",
        "statistical outliers",
        "edge cases",
        "boundary conditions",
        "limit testing",
        "capacity analysis",
        "threshold breaches"
    ]
    
    # Natural language variations (10)
    natural_variations = [
        "gimme all dem students yo",
        "sup how many peeps we got",
        "yo check the fam members count",
        "wassup with approved apps",
        "show me whatcha got on cities",
        "lemme see those high schools",
        "can u plz count students 4 me",
        "I need to know about applications status",
        "Would you kindly retrieve student information",
        "Please be so kind as to enumerate the family members"
    ]
    
    # Combine all query categories
    all_queries = (
        basic_counts +
        relationship_queries +
        aggregation_queries +
        bizarre_specific +
        join_queries +
        datetime_queries +
        status_queries +
        performance_queries +
        natural_variations
    )
    
    # Shuffle for randomness
    random.shuffle(all_queries)
    
    # Create query objects with IDs
    queries = [
        {"id": i+1, "query": q, "category": categorize_query(q)}
        for i, q in enumerate(all_queries[:200])  # Ensure exactly 200
    ]
    
    return queries

def categorize_query(query: str) -> str:
    """Categorize query for analysis"""
    query_lower = query.lower()
    if "count" in query_lower or "how many" in query_lower:
        return "counting"
    elif "join" in query_lower or "with their" in query_lower:
        return "joining"
    elif "group" in query_lower or "by" in query_lower:
        return "grouping"
    elif "average" in query_lower or "sum" in query_lower or "max" in query_lower:
        return "aggregation"
    elif "show" in query_lower or "display" in query_lower:
        return "selection"
    elif any(word in query_lower for word in ["zombie", "ghost", "time travel", "bizarre"]):
        return "bizarre"
    elif any(word in query_lower for word in ["today", "month", "year", "date"]):
        return "temporal"
    elif any(word in query_lower for word in ["status", "pending", "approved", "rejected"]):
        return "status"
    else:
        return "other"

def execute_query(query_text: str, connection_id: int = 1) -> Dict[str, Any]:
    """Execute a single query and return results with timing"""
    start_time = time.time()
    
    payload = {
        "prompt": query_text,
        "connection_id": connection_id
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response_time": (end_time - start_time) * 1000,  # in ms
                "sql": result.get("generated_sql"),
                "method": result.get("metadata", {}).get("method", "unknown"),
                "has_results": bool(result.get("results")),
                "error": None
            }
        else:
            return {
                "success": False,
                "response_time": (end_time - start_time) * 1000,
                "sql": None,
                "method": None,
                "has_results": False,
                "error": f"HTTP {response.status_code}"
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "response_time": 30000,  # timeout value
            "sql": None,
            "method": None,
            "has_results": False,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "response_time": 0,
            "sql": None,
            "method": None,
            "has_results": False,
            "error": str(e)
        }

def run_performance_test():
    """Run the complete performance test with 200 queries"""
    print("=" * 80)
    print("PERFORMANCE TEST: 200 BIZARRE QUERIES")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Generate queries
    print("Generating 200 bizarre queries...")
    queries = generate_bizarre_queries()
    print(f"✓ Generated {len(queries)} queries across multiple categories")
    print()
    
    # Initialize results tracking
    results = []
    success_count = 0
    failure_count = 0
    response_times = []
    methods_used = {"pattern_matching": 0, "llm_optimized": 0, "unknown": 0, "error": 0}
    category_stats = {}
    
    # Progress bar setup
    print("Executing queries...")
    print("-" * 80)
    
    # Execute each query
    for i, query_obj in enumerate(queries, 1):
        query_id = query_obj["id"]
        query_text = query_obj["query"]
        category = query_obj["category"]
        
        # Show progress every 20 queries
        if i % 20 == 0:
            print(f"Progress: {i}/{len(queries)} ({i/len(queries)*100:.1f}%)")
        
        # Execute query
        result = execute_query(query_text)
        
        # Track results
        results.append({
            "id": query_id,
            "query": query_text,
            "category": category,
            **result
        })
        
        if result["success"]:
            success_count += 1
            response_times.append(result["response_time"])
            method = result["method"] or "unknown"
            methods_used[method] = methods_used.get(method, 0) + 1
        else:
            failure_count += 1
            methods_used["error"] = methods_used.get("error", 0) + 1
        
        # Track category statistics
        if category not in category_stats:
            category_stats[category] = {"total": 0, "success": 0, "failures": 0, "avg_time": []}
        
        category_stats[category]["total"] += 1
        if result["success"]:
            category_stats[category]["success"] += 1
            category_stats[category]["avg_time"].append(result["response_time"])
        else:
            category_stats[category]["failures"] += 1
    
    print(f"Progress: {len(queries)}/{len(queries)} (100%)")
    print()
    
    # Calculate statistics
    print("=" * 80)
    print("PERFORMANCE STATISTICS")
    print("=" * 80)
    print()
    
    print("Overall Results:")
    print(f"  Total Queries: {len(queries)}")
    print(f"  Successful: {success_count} ({success_count/len(queries)*100:.1f}%)")
    print(f"  Failed: {failure_count} ({failure_count/len(queries)*100:.1f}%)")
    print()
    
    if response_times:
        print("Response Time Statistics (ms):")
        print(f"  Min: {min(response_times):.2f}")
        print(f"  Max: {max(response_times):.2f}")
        print(f"  Mean: {statistics.mean(response_times):.2f}")
        print(f"  Median: {statistics.median(response_times):.2f}")
        if len(response_times) > 1:
            print(f"  Std Dev: {statistics.stdev(response_times):.2f}")
        
        # Percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times)//2]
        p90 = sorted_times[int(len(sorted_times)*0.9)]
        p95 = sorted_times[int(len(sorted_times)*0.95)]
        p99 = sorted_times[int(len(sorted_times)*0.99)] if len(sorted_times) > 100 else sorted_times[-1]
        
        print(f"  P50: {p50:.2f}")
        print(f"  P90: {p90:.2f}")
        print(f"  P95: {p95:.2f}")
        print(f"  P99: {p99:.2f}")
    print()
    
    print("Methods Used:")
    for method, count in methods_used.items():
        if count > 0:
            print(f"  {method}: {count} ({count/len(queries)*100:.1f}%)")
    print()
    
    print("Performance by Category:")
    print("-" * 80)
    print(f"{'Category':<15} {'Total':<8} {'Success':<8} {'Failed':<8} {'Success %':<12} {'Avg Time (ms)':<15}")
    print("-" * 80)
    
    for category, stats in sorted(category_stats.items()):
        success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        avg_time = statistics.mean(stats["avg_time"]) if stats["avg_time"] else 0
        print(f"{category:<15} {stats['total']:<8} {stats['success']:<8} {stats['failures']:<8} {success_rate:<12.1f} {avg_time:<15.2f}")
    
    print()
    
    # Show sample of failed queries
    failed_queries = [r for r in results if not r["success"]]
    if failed_queries:
        print("Sample Failed Queries (first 10):")
        print("-" * 80)
        for fq in failed_queries[:10]:
            print(f"  Query: {fq['query'][:60]}...")
            print(f"  Error: {fq['error']}")
            print()
    
    # Show sample of slowest queries
    if response_times:
        slowest = sorted([r for r in results if r["success"]], key=lambda x: x["response_time"], reverse=True)[:5]
        print("Slowest Queries (top 5):")
        print("-" * 80)
        for sq in slowest:
            print(f"  Query: {sq['query'][:60]}...")
            print(f"  Time: {sq['response_time']:.2f}ms")
            print(f"  Method: {sq['method']}")
            print()
    
    # Show sample of fastest queries
    if response_times:
        fastest = sorted([r for r in results if r["success"]], key=lambda x: x["response_time"])[:5]
        print("Fastest Queries (top 5):")
        print("-" * 80)
        for fq in fastest:
            print(f"  Query: {fq['query'][:60]}...")
            print(f"  Time: {fq['response_time']:.2f}ms")
            print(f"  Method: {fq['method']}")
            print()
    
    # Save detailed results to file
    with open("performance_test_results.json", "w") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "summary": {
                "total_queries": len(queries),
                "successful": success_count,
                "failed": failure_count,
                "success_rate": success_count/len(queries)*100,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "methods_used": methods_used,
                "category_stats": category_stats
            },
            "detailed_results": results
        }, f, indent=2)
    
    print("=" * 80)
    print("TEST COMPLETED")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Detailed results saved to: performance_test_results.json")
    print("=" * 80)

if __name__ == "__main__":
    run_performance_test()