#!/usr/bin/env python3
"""
Generate and test 500 diverse queries to stress test the RAG SQL system.
Tests tables, indexes, relations, enums, and various SQL patterns.
"""

import json
import time
import requests
from typing import List, Dict, Any
from datetime import datetime
import random

# API Configuration
BASE_URL = "http://localhost:8000/api"
CONNECTION_ID = 1

def generate_test_queries() -> List[str]:
    """Generate 500 diverse test queries"""
    queries = []
    
    # 1. Basic counting queries (50)
    entities = ["students", "applications", "cities", "states", "documents", 
                "family members", "schools", "addresses", "recommendations"]
    for entity in entities:
        queries.extend([
            f"count {entity}",
            f"count all {entity}",
            f"how many {entity}",
            f"total {entity}",
            f"number of {entity}",
            f"show count of {entity}"
        ])
    
    # 2. Location-based queries with accents (40)
    cities = ["Bayamón", "San Juan", "Ponce", "Carolina", "Caguas", 
              "Arecibo", "Guaynabo", "Mayagüez", "Trujillo Alto", "San Sebastián"]
    for city in cities:
        queries.extend([
            f"count students from {city}",
            f"students living in {city}",
            f"applications from {city}",
            f"show students from {city}",
        ])
    
    # 3. Status-based queries using enums (50)
    statuses = ["pending", "submitted", "under review", "approved", "rejected", "cancelled"]
    for status in statuses:
        queries.extend([
            f"count students with {status} application",
            f"show {status} applications",
            f"students with application {status}",
            f"list {status} scholarship applications",
            f"how many {status} applications",
            f"total applications {status}",
            f"find all {status} applications",
            f"get {status} application count"
        ])
    
    # 4. Relationship queries (JOIN operations) (60)
    queries.extend([
        "students with applications",
        "students without applications",
        "students with family members",
        "students without family members",
        "students with documents",
        "students without documents",
        "students with recommendations",
        "students without recommendations",
        "applications with documents",
        "applications without documents",
        "students with approved applications",
        "students with rejected applications",
        "students with pending applications",
        "students with multiple applications",
        "students with single application",
        "students with more than 2 family members",
        "students with less than 3 family members",
        "students with exactly 1 family member",
        "applications with all documents",
        "applications missing documents",
        "students from Bayamón with applications",
        "students from San Juan without applications",
        "rejected applications from Ponce",
        "approved applications from Carolina",
        "pending applications from Caguas",
        "students with birth certificate",
        "students without birth certificate",
        "students with academic transcript",
        "students without academic transcript",
        "students with recommendation letter",
        "students without recommendation letter",
        "students with declaracion jurada",
        "students without declaracion jurada",
        "applications with birth certificate submitted",
        "applications without birth certificate",
        "students with complete documentation",
        "students with incomplete documentation",
        "applications submitted this year",
        "applications submitted last year",
        "recent applications",
        "old applications",
        "students with recent applications",
        "students with old applications",
        "active students with applications",
        "inactive students with applications",
        "students with family in same city",
        "students with family in different city",
        "applications with high scores",
        "applications with low scores",
        "students with high GPA",
        "students with low GPA",
        "applications from rural areas",
        "applications from urban areas",
        "students with financial need",
        "students without financial need",
        "applications with priority status",
        "applications without priority status",
        "students with special conditions",
        "students without special conditions"
    ])
    
    # 5. Aggregation queries (40)
    queries.extend([
        "average family members per student",
        "maximum applications per student",
        "minimum applications per student",
        "total applications per city",
        "count students per city",
        "count applications per status",
        "average age of students",
        "oldest student",
        "youngest student",
        "most common city",
        "least common city",
        "most common application status",
        "total documents per student",
        "average documents per application",
        "students grouped by city",
        "applications grouped by status",
        "students grouped by document count",
        "applications grouped by month",
        "students by application count",
        "cities by student count",
        "status distribution",
        "document type distribution",
        "family size distribution",
        "age distribution",
        "application timeline",
        "submission patterns",
        "approval rate",
        "rejection rate",
        "completion rate",
        "document submission rate",
        "average processing time",
        "peak submission months",
        "geographic distribution",
        "demographic breakdown",
        "application trends",
        "success metrics",
        "performance indicators",
        "statistical summary",
        "quarterly reports",
        "annual summary"
    ])
    
    # 6. Complex filtering queries (50)
    queries.extend([
        "students from Bayamón with rejected applications",
        "students from San Juan with approved applications and complete documents",
        "pending applications from students with more than 3 family members",
        "rejected applications from single parent families",
        "approved applications with all documents submitted before deadline",
        "students from Ponce or Carolina with applications",
        "students from Bayamón and Caguas",
        "applications submitted in January or February",
        "students aged 18 to 25 with applications",
        "female students with approved applications",
        "male students with rejected applications",
        "students with GPA above 3.5",
        "students with GPA below 2.5",
        "applications with missing birth certificate or transcript",
        "students with either approved or pending applications",
        "applications neither approved nor rejected",
        "students not from San Juan",
        "applications not in pending status",
        "students without applications from major cities",
        "rural students with complete documentation",
        "urban students with incomplete documentation",
        "first time applicants",
        "repeat applicants",
        "students who reapplied after rejection",
        "successful reapplications",
        "applications with expedited processing",
        "applications with normal processing",
        "high priority applications",
        "low priority applications",
        "applications requiring review",
        "applications ready for approval",
        "incomplete applications older than 30 days",
        "complete applications waiting for review",
        "recently submitted applications",
        "applications close to deadline",
        "overdue applications",
        "applications with extensions",
        "students with multiple addresses",
        "students with single address",
        "applications with verification pending",
        "applications with verification complete",
        "students eligible for scholarship",
        "students not eligible for scholarship",
        "applications meeting all criteria",
        "applications missing criteria",
        "borderline applications",
        "exceptional applications",
        "standard applications",
        "special case applications",
        "priority review applications"
    ])
    
    # 7. Pattern matching queries (40)
    queries.extend([
        "students whose name starts with A",
        "students whose name ends with z",
        "students whose name contains Maria",
        "cities starting with San",
        "cities ending with o",
        "cities containing Bay",
        "students with gmail email",
        "students with yahoo email",
        "students with edu email",
        "applications with notes containing urgent",
        "applications with notes containing review",
        "documents with type containing certificate",
        "addresses containing Ave",
        "addresses containing Street",
        "addresses containing Calle",
        "phone numbers starting with 787",
        "phone numbers starting with 939",
        "emails containing student",
        "names with accents",
        "cities with accents",
        "spanish surnames",
        "english surnames",
        "compound names",
        "hyphenated surnames",
        "Jr or Sr in names",
        "middle names present",
        "no middle names",
        "postal codes starting with 00",
        "specific zip codes",
        "area codes 787",
        "area codes 939",
        "international phone numbers",
        "local phone numbers",
        "mobile numbers",
        "landline numbers",
        "government emails",
        "personal emails",
        "business emails",
        "educational institution emails"
    ])
    
    # 8. Date and time queries (40)
    queries.extend([
        "applications submitted today",
        "applications submitted yesterday",
        "applications submitted this week",
        "applications submitted last week",
        "applications submitted this month",
        "applications submitted last month",
        "applications submitted this year",
        "applications submitted last year",
        "applications submitted in January",
        "applications submitted in December",
        "applications submitted on weekends",
        "applications submitted on weekdays",
        "morning submissions",
        "afternoon submissions",
        "evening submissions",
        "night submissions",
        "applications by day of week",
        "applications by hour of day",
        "peak submission times",
        "quiet submission periods",
        "applications before deadline",
        "applications after deadline",
        "on-time submissions",
        "late submissions",
        "early submissions",
        "last minute submissions",
        "submissions in Q1",
        "submissions in Q2",
        "submissions in Q3",
        "submissions in Q4",
        "fiscal year submissions",
        "academic year submissions",
        "summer applications",
        "winter applications",
        "spring applications",
        "fall applications",
        "holiday period submissions",
        "business day submissions",
        "processing time by month",
        "approval time trends"
    ])
    
    # 9. Comparison queries (30)
    queries.extend([
        "more students from Bayamón or San Juan",
        "compare approved vs rejected applications",
        "students with most family members",
        "students with least family members",
        "city with most applications",
        "city with least applications",
        "busiest application month",
        "slowest application month",
        "highest approval rate by city",
        "lowest approval rate by city",
        "compare male vs female applicants",
        "compare urban vs rural applicants",
        "fastest processing times",
        "slowest processing times",
        "most complete applications",
        "least complete applications",
        "highest scoring applications",
        "lowest scoring applications",
        "most common rejection reason",
        "most common approval factor",
        "best performing schools",
        "worst performing schools",
        "top 10 students by GPA",
        "bottom 10 students by GPA",
        "top 5 cities by applications",
        "bottom 5 cities by applications",
        "leading application sources",
        "trailing application sources",
        "year over year comparison",
        "month over month comparison"
    ])
    
    # 10. Existence queries (30)
    queries.extend([
        "are there any rejected applications",
        "are there any approved applications",
        "are there students from Bayamón",
        "are there students without applications",
        "do we have applications from San Juan",
        "exist students with complete documents",
        "exist applications in pending status",
        "any students with more than 5 family members",
        "any applications submitted today",
        "any overdue applications",
        "check if students from Ponce exist",
        "check if rejected applications exist",
        "verify students with documents",
        "verify applications with all criteria met",
        "confirm pending applications present",
        "confirm approved applications present",
        "validate student records exist",
        "validate application records exist",
        "find if duplicates exist",
        "find if incomplete records exist",
        "identify missing data",
        "identify data gaps",
        "locate orphan records",
        "locate unlinked documents",
        "discover anomalies",
        "discover patterns",
        "detect issues",
        "detect problems",
        "spot trends",
        "spot outliers"
    ])
    
    # 11. Limit and pagination queries (20)
    queries.extend([
        "first 10 students",
        "last 10 students",
        "top 5 applications",
        "bottom 5 applications",
        "show 20 students",
        "display 15 applications",
        "list 25 cities",
        "get 30 documents",
        "fetch 10 recent applications",
        "retrieve 5 pending applications",
        "next 10 students",
        "previous 10 students",
        "page 2 of students",
        "page 3 of applications",
        "students 11 to 20",
        "applications 21 to 30",
        "skip first 10 students",
        "skip first 20 applications",
        "limit to 100 results",
        "maximum 50 records"
    ])
    
    # 12. Null and empty queries (20)
    queries.extend([
        "students with null email",
        "students with empty phone",
        "applications with null status",
        "documents with empty type",
        "students without email",
        "students without phone",
        "applications without notes",
        "documents without date",
        "missing student data",
        "missing application data",
        "incomplete student records",
        "incomplete application records",
        "blank fields in students",
        "blank fields in applications",
        "null values in database",
        "empty values in database",
        "required fields missing",
        "optional fields missing",
        "data quality issues",
        "data completeness check"
    ])
    
    # 13. Special character and accent queries (20)
    queries.extend([
        "students from Mayagüez",
        "students from Añasco",
        "students from Peñuelas",
        "students from Río Grande",
        "students from Canóvanas",
        "students with ñ in name",
        "students with á in name",
        "students with é in name",
        "students with í in name",
        "students with ó in name",
        "students with ú in name",
        "students with ü in name",
        "cities with accents",
        "names with tildes",
        "Spanish special characters",
        "Latin characters in data",
        "Unicode support test",
        "international characters",
        "diacritical marks present",
        "accent-sensitive search"
    ])
    
    # 14. System and metadata queries (20)
    queries.extend([
        "table statistics",
        "index usage",
        "relationship mappings",
        "enum definitions",
        "schema information",
        "database size",
        "record counts",
        "table sizes",
        "index effectiveness",
        "query performance",
        "slow queries",
        "fast queries",
        "optimization opportunities",
        "missing indexes",
        "unused indexes",
        "foreign key constraints",
        "data integrity check",
        "referential integrity",
        "constraint violations",
        "data consistency"
    ])
    
    # 15. Business logic queries (30)
    queries.extend([
        "eligible students for scholarship",
        "ineligible students for scholarship",
        "qualified applicants",
        "unqualified applicants",
        "students meeting requirements",
        "students not meeting requirements",
        "applications ready for review",
        "applications needing more info",
        "high priority cases",
        "low priority cases",
        "urgent applications",
        "standard applications",
        "expedited processing candidates",
        "normal processing queue",
        "review queue",
        "approval queue",
        "rejection candidates",
        "borderline cases",
        "exceptional cases",
        "standard cases",
        "special circumstances",
        "hardship cases",
        "merit-based selections",
        "need-based selections",
        "automatic approvals",
        "automatic rejections",
        "manual review required",
        "supervisor approval needed",
        "documentation verification pending",
        "final decision pending"
    ])
    
    # Ensure we have exactly 500 queries
    while len(queries) < 500:
        # Add variations of existing queries
        base_queries = [
            "count students from {city}",
            "show {status} applications",
            "students with {document_type}",
            "applications from {month}",
            "top {n} students by {metric}"
        ]
        
        cities = ["Aguadilla", "Isabela", "Camuy", "Hatillo", "Barceloneta"]
        statuses = ["draft", "in progress", "completed", "expired", "withdrawn"]
        doc_types = ["ID card", "proof of income", "residence proof", "grade report"]
        months = ["March", "April", "May", "June", "July"]
        metrics = ["score", "ranking", "performance", "attendance", "participation"]
        
        for base in base_queries:
            if len(queries) >= 500:
                break
            if "{city}" in base:
                queries.append(base.format(city=random.choice(cities)))
            elif "{status}" in base:
                queries.append(base.format(status=random.choice(statuses)))
            elif "{document_type}" in base:
                queries.append(base.format(document_type=random.choice(doc_types)))
            elif "{month}" in base:
                queries.append(base.format(month=random.choice(months)))
            elif "{n}" in base and "{metric}" in base:
                queries.append(base.format(n=random.randint(3, 20), metric=random.choice(metrics)))
    
    return queries[:500]  # Ensure exactly 500


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
            return {
                "prompt": prompt,
                "status": "success",
                "execution_time": execution_time,
                "generated_sql": result.get("generated_sql"),
                "result_type": result.get("result_type"),
                "row_count": len(result.get("result_data", {}).get("data", [])) if isinstance(result.get("result_data"), dict) else 0,
                "uses_index": "WITH (INDEX" in result.get("generated_sql", ""),
                "uses_join": "JOIN" in result.get("generated_sql", ""),
                "uses_where": "WHERE" in result.get("generated_sql", ""),
                "uses_group": "GROUP BY" in result.get("generated_sql", ""),
                "uses_enum": "Status =" in result.get("generated_sql", "") or "Status IN" in result.get("generated_sql", ""),
                "uses_collate": "COLLATE" in result.get("generated_sql", "")
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


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze test results and generate statistics"""
    total = len(results)
    successful = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    timeouts = sum(1 for r in results if r["status"] == "timeout")
    
    # Feature usage statistics for successful queries
    success_results = [r for r in results if r["status"] == "success"]
    
    stats = {
        "total_queries": total,
        "successful": successful,
        "errors": errors,
        "timeouts": timeouts,
        "success_rate": f"{(successful/total)*100:.1f}%",
        "error_rate": f"{(errors/total)*100:.1f}%",
        "timeout_rate": f"{(timeouts/total)*100:.1f}%",
        
        "feature_usage": {
            "uses_index": sum(1 for r in success_results if r.get("uses_index")),
            "uses_join": sum(1 for r in success_results if r.get("uses_join")),
            "uses_where": sum(1 for r in success_results if r.get("uses_where")),
            "uses_group": sum(1 for r in success_results if r.get("uses_group")),
            "uses_enum": sum(1 for r in success_results if r.get("uses_enum")),
            "uses_collate": sum(1 for r in success_results if r.get("uses_collate"))
        },
        
        "performance": {
            "avg_execution_time": sum(r["execution_time"] for r in success_results) / len(success_results) if success_results else 0,
            "min_execution_time": min((r["execution_time"] for r in success_results), default=0),
            "max_execution_time": max((r["execution_time"] for r in success_results), default=0),
            "median_execution_time": sorted([r["execution_time"] for r in success_results])[len(success_results)//2] if success_results else 0
        },
        
        "result_types": {},
        "error_types": {}
    }
    
    # Count result types
    for r in success_results:
        result_type = r.get("result_type", "unknown")
        stats["result_types"][result_type] = stats["result_types"].get(result_type, 0) + 1
    
    # Count error types
    for r in results:
        if r["status"] == "error":
            error_type = r.get("error", "unknown")[:50]  # Truncate long errors
            stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1
    
    return stats


def main():
    """Main test execution"""
    print("=" * 80)
    print("RAG SQL Query System - 500 Query Stress Test")
    print("=" * 80)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Endpoint: {BASE_URL}")
    print(f"Connection ID: {CONNECTION_ID}")
    print("=" * 80)
    
    # Generate test queries
    print("\n📝 Generating 500 test queries...")
    queries = generate_test_queries()
    print(f"✅ Generated {len(queries)} unique test queries")
    
    # Test queries
    print("\n🧪 Testing queries...")
    print("This may take several minutes. Progress will be shown every 50 queries.")
    
    results = []
    start_time = time.time()
    
    for i, query in enumerate(queries, 1):
        result = test_query(query)
        results.append(result)
        
        # Show progress every 50 queries
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            remaining = (500 - i) / rate
            print(f"  Progress: {i}/500 ({i/5:.0f}%) - "
                  f"Rate: {rate:.1f} q/s - "
                  f"ETA: {remaining/60:.1f} min")
    
    total_time = time.time() - start_time
    
    # Analyze results
    print("\n📊 Analyzing results...")
    stats = analyze_results(results)
    
    # Save detailed results
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "summary": stats,
            "queries": results,
            "metadata": {
                "total_time": total_time,
                "queries_per_second": len(queries) / total_time,
                "timestamp": datetime.now().isoformat()
            }
        }, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    print(f"\n📈 Overall Statistics:")
    print(f"  Total Queries: {stats['total_queries']}")
    print(f"  Successful: {stats['successful']} ({stats['success_rate']})")
    print(f"  Errors: {stats['errors']} ({stats['error_rate']})")
    print(f"  Timeouts: {stats['timeouts']} ({stats['timeout_rate']})")
    
    print(f"\n⚡ Performance Metrics:")
    print(f"  Total Test Time: {total_time:.1f} seconds")
    print(f"  Queries per Second: {len(queries)/total_time:.1f}")
    print(f"  Avg Execution Time: {stats['performance']['avg_execution_time']:.0f} ms")
    print(f"  Min Execution Time: {stats['performance']['min_execution_time']} ms")
    print(f"  Max Execution Time: {stats['performance']['max_execution_time']} ms")
    print(f"  Median Execution Time: {stats['performance']['median_execution_time']} ms")
    
    print(f"\n🔧 Feature Usage (out of {stats['successful']} successful queries):")
    for feature, count in stats['feature_usage'].items():
        percentage = (count / stats['successful'] * 100) if stats['successful'] > 0 else 0
        print(f"  {feature}: {count} ({percentage:.1f}%)")
    
    print(f"\n📋 Result Types:")
    for result_type, count in stats['result_types'].items():
        print(f"  {result_type}: {count}")
    
    if stats['error_types']:
        print(f"\n❌ Error Types:")
        for error_type, count in sorted(stats['error_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {error_type}: {count}")
    
    # Find interesting queries
    print(f"\n🌟 Interesting Findings:")
    
    # Fastest successful queries
    fast_queries = sorted([r for r in results if r["status"] == "success"], 
                         key=lambda x: x["execution_time"])[:5]
    print("\n  Fastest Queries:")
    for q in fast_queries:
        print(f"    - {q['prompt'][:50]}... ({q['execution_time']} ms)")
    
    # Slowest successful queries
    slow_queries = sorted([r for r in results if r["status"] == "success"], 
                         key=lambda x: x["execution_time"], reverse=True)[:5]
    print("\n  Slowest Queries:")
    for q in slow_queries:
        print(f"    - {q['prompt'][:50]}... ({q['execution_time']} ms)")
    
    # Complex queries (using multiple features)
    complex_queries = [r for r in results if r["status"] == "success" and 
                      sum([r.get("uses_join", False), r.get("uses_where", False),
                           r.get("uses_group", False), r.get("uses_enum", False)]) >= 3]
    if complex_queries:
        print(f"\n  Most Complex Queries ({len(complex_queries)} total):")
        for q in complex_queries[:5]:
            features = []
            if q.get("uses_join"): features.append("JOIN")
            if q.get("uses_where"): features.append("WHERE")
            if q.get("uses_group"): features.append("GROUP")
            if q.get("uses_enum"): features.append("ENUM")
            if q.get("uses_collate"): features.append("COLLATE")
            print(f"    - {q['prompt'][:40]}... [{', '.join(features)}]")
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()