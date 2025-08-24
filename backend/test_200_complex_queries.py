#!/usr/bin/env python3
"""
Test with 200 TECHNICALLY COMPLEX queries that challenge SQL generation
Focus on complex SQL logic, not weird wording
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

def generate_complex_queries() -> List[Dict[str, str]]:
    """Generate 200 technically complex SQL queries"""
    queries = []
    
    # Complex JOIN queries (40)
    multi_join_queries = [
        "show students with their city, region, and municipio names",
        "list all students with their family members and the family members' occupations",
        "get students with their scholarship application status and the reviewing board members",
        "show family members with their students and the students' high schools",
        "display students with all their documents and document types",
        "find students with their addresses including city, region, and country details",
        "show all relationships between students and their legal guardians with guardian occupations",
        "list students with their application history and all status changes",
        "get family trees showing students, parents, and siblings in one query",
        "show students with their academic records and the schools they attended",
        "display all users with their roles and the permissions for each role",
        "find students linked to multiple family members with different relationships",
        "show scholarship applications with student details, family income, and recommendations",
        "get students with their emergency contacts and contact relationships",
        "list all audit logs with user details and the affected student records",
        "show document submissions with student info, document type, and verification status",
        "find students with incomplete applications and missing document types",
        "display family members who are also students in the system",
        "get circular references where students are family members of other students",
        "show all many-to-many relationships between students and programs",
        "list students with their counselors and counselor's other students",
        "find shared addresses between different students and family members",
        "show inheritance of attributes from parent to child records",
        "get transitive relationships through multiple join tables",
        "display students connected through common family members",
        "find all second-degree relationships in the family network",
        "show students with same last name but different families",
        "get all polymorphic associations in the user system",
        "list records with composite foreign keys",
        "show self-referential joins in family relationships",
        "find bridging tables connecting multiple entities",
        "display hierarchical data with parent-child relationships",
        "get network graph of all student connections",
        "show students related through multiple paths",
        "find isolated student records with no relationships",
        "display maximum relationship depth in family trees",
        "get students with cross-referenced documents",
        "show parallel relationships between same entities",
        "find redundant relationship paths",
        "display students with conflicting relationship data"
    ]
    
    # Complex aggregation queries (35)
    aggregation_queries = [
        "calculate average family size grouped by city and region",
        "find the median age of students per high school",
        "compute standard deviation of application scores by region",
        "calculate percentile rankings of students by GPA",
        "find correlation between family income and scholarship approval",
        "compute year-over-year growth rate of applications",
        "calculate cumulative sum of approvals by month",
        "find mode of family member ages per household",
        "compute variance in processing times by application type",
        "calculate weighted average of scores by credit hours",
        "find geometric mean of sequential growth rates",
        "compute harmonic mean of rate-based metrics",
        "calculate coefficient of variation for each metric",
        "find z-scores for student performance metrics",
        "compute confidence intervals for approval rates",
        "calculate moving averages over 3, 6, and 12 month windows",
        "find exponential moving average of applications",
        "compute compound annual growth rate of enrollments",
        "calculate interquartile range of family incomes",
        "find outliers using 1.5 * IQR rule",
        "compute skewness and kurtosis of distributions",
        "calculate Gini coefficient for income inequality",
        "find Pareto distribution of top performers",
        "compute Shannon entropy of categorical distributions",
        "calculate chi-square test statistics",
        "find covariance matrix between multiple variables",
        "compute eigenvectors of correlation matrix",
        "calculate principal components of student features",
        "find clusters using distance metrics",
        "compute silhouette scores for groupings",
        "calculate lift and support for association rules",
        "find seasonal decomposition of time series",
        "compute autocorrelation of sequential data",
        "calculate cross-correlation between series",
        "find Fourier transform of periodic patterns"
    ]
    
    # Window function queries (30)
    window_queries = [
        "rank students by GPA within each high school",
        "calculate running total of applications per day",
        "find dense rank of students by application score",
        "compute row number partitioned by city and ordered by age",
        "calculate percent rank of family income within regions",
        "find cumulative distribution of student ages",
        "compute lag and lead values for time series comparison",
        "calculate ntile quartiles of performance metrics",
        "find first and last values in ordered groups",
        "compute nth value in sliding windows",
        "calculate difference from group average for each student",
        "find percentage of total within categories",
        "compute rank without gaps using dense rank",
        "calculate moving sum over last 7 records",
        "find previous and next record values",
        "compute cumulative count with reset conditions",
        "calculate expanding window statistics",
        "find gaps and islands in sequential data",
        "compute session windows with timeout logic",
        "calculate tumbling windows for streaming data",
        "find overlapping window aggregations",
        "compute hopping windows with custom stride",
        "calculate range between current and preceding rows",
        "find peers within value ranges",
        "compute relative position in sorted groups",
        "calculate running variance and standard deviation",
        "find local maxima and minima in windows",
        "compute window frame with exclusion",
        "calculate custom window boundaries",
        "find pattern matching across windows"
    ]
    
    # Subquery and CTE queries (25)
    subquery_queries = [
        "find students with above average GPA in their school",
        "get family members with more dependents than average",
        "show applications with processing time above 90th percentile",
        "find students in top 10% of their graduating class",
        "get regions with approval rate higher than national average",
        "show cities with more students than median city size",
        "find outlier families by income using nested statistics",
        "get students with scores better than their school average",
        "show documents submitted faster than typical processing",
        "find anomalous patterns using multiple subqueries",
        "get hierarchical totals using recursive CTEs",
        "show path from student to root in family tree",
        "find all descendants of a family patriarch",
        "get transitive closure of relationships",
        "show bill of materials explosion for requirements",
        "find connected components in relationship graph",
        "get shortest path between related students",
        "show breadth-first traversal of connections",
        "find depth-first search results in hierarchy",
        "get topological sort of dependencies",
        "show strongly connected components",
        "find bridges and articulation points",
        "get minimum spanning tree of relationships",
        "show maximum flow in application pipeline",
        "find critical path in process workflow"
    ]
    
    # Complex conditional logic queries (25)
    conditional_queries = [
        "categorize students using nested CASE statements with multiple conditions",
        "apply complex business rules with multiple WHEN clauses",
        "implement decision trees using cascading conditions",
        "calculate scores using weighted multi-criteria evaluation",
        "find eligibility using compound boolean expressions",
        "apply different formulas based on category combinations",
        "implement finite state machine transitions in SQL",
        "calculate tiered pricing with boundary conditions",
        "find matching using fuzzy logic rules",
        "apply temporal versioning with effective dates",
        "implement slowly changing dimension type 2 logic",
        "calculate pro-rated amounts with multiple factors",
        "find conflicts using complex constraint checking",
        "apply validation rules with exception handling",
        "implement approval workflow with state transitions",
        "calculate dynamic thresholds based on context",
        "find anomalies using statistical process control",
        "apply regulatory compliance rules",
        "implement role-based access control logic",
        "calculate risk scores using multiple factors",
        "find optimization using constraint satisfaction",
        "apply machine learning decision boundaries",
        "implement recommendation engine logic",
        "calculate similarity scores with multiple metrics",
        "find best matches using preference rankings"
    ]
    
    # Set operations and complex filtering (20)
    set_operations = [
        "find students in city A but not in city B using EXCEPT",
        "get union of active and pending applications",
        "show intersection of high achievers and scholarship recipients",
        "find symmetric difference between two student groups",
        "get students satisfying any of 5 complex criteria using OR",
        "show records meeting all of 7 conditions using AND",
        "find mutually exclusive groups using NOT EXISTS",
        "get records present in all specified tables",
        "show partial matches using IN with subqueries",
        "find records absent from any related table",
        "get Cartesian product with filtering",
        "show semi-join results without duplicates",
        "find anti-join patterns",
        "get full outer join with null handling",
        "show natural join with ambiguity resolution",
        "find cross apply results with table functions",
        "get outer apply with default values",
        "show lateral join with correlated subqueries",
        "find pivot results with dynamic columns",
        "get unpivot of normalized data"
    ]
    
    # Date/Time complexity queries (15)
    datetime_queries = [
        "calculate business days between application and approval excluding holidays",
        "find applications submitted in last fiscal quarter",
        "get age in years, months, and days at time of application",
        "show timezone-aware timestamp conversions",
        "calculate duration using date arithmetic with leap years",
        "find overlapping date ranges between records",
        "get records with dates in multiple calendars",
        "show temporal joins with validity periods",
        "calculate sliding time windows with custom intervals",
        "find gaps in temporal sequences",
        "get period-over-period comparisons with alignment",
        "show seasonality adjustments in time series",
        "calculate custom fiscal periods",
        "find temporal dependencies and prerequisites",
        "get point-in-time snapshots of data"
    ]
    
    # Advanced string manipulation queries (10)
    string_queries = [
        "parse complex formatted strings using SUBSTRING and CHARINDEX",
        "extract patterns using regular expressions",
        "calculate edit distance between strings",
        "find phonetic matches using SOUNDEX",
        "get longest common subsequence",
        "show string similarity using trigrams",
        "calculate Levenshtein distance for fuzzy matching",
        "find palindromes using string reversal",
        "get formatted output with complex concatenation",
        "show text analysis with word frequency"
    ]
    
    # Performance-challenging queries (10)
    performance_queries = [
        "find all possible paths in graph with cycle detection",
        "calculate factorial using recursive CTE",
        "get Fibonacci sequence up to nth term",
        "show prime numbers using sieve algorithm",
        "find traveling salesman approximation",
        "calculate matrix multiplication in SQL",
        "get convex hull of geographic points",
        "show Voronoi diagram regions",
        "find k-means clustering results",
        "calculate PageRank scores for network"
    ]
    
    # Combine all categories
    all_queries = (
        multi_join_queries +
        aggregation_queries +
        window_queries +
        subquery_queries +
        conditional_queries +
        set_operations +
        datetime_queries +
        string_queries +
        performance_queries
    )
    
    # Ensure we have exactly 200
    all_queries = all_queries[:200]
    
    # Create query objects
    queries = [
        {
            "id": i+1,
            "query": q,
            "complexity": calculate_complexity(q)
        }
        for i, q in enumerate(all_queries)
    ]
    
    return queries

def calculate_complexity(query: str) -> str:
    """Calculate query complexity level"""
    query_lower = query.lower()
    
    complexity_score = 0
    
    # Check for complex SQL features
    if any(word in query_lower for word in ["recursive", "cte", "with", "lateral"]):
        complexity_score += 3
    if any(word in query_lower for word in ["window", "over", "partition", "rank", "dense_rank"]):
        complexity_score += 3
    if any(word in query_lower for word in ["stddev", "variance", "correlation", "percentile"]):
        complexity_score += 2
    if any(word in query_lower for word in ["union", "except", "intersect", "minus"]):
        complexity_score += 2
    if any(word in query_lower for word in ["pivot", "unpivot", "cross apply", "outer apply"]):
        complexity_score += 3
    if "subquery" in query_lower or "nested" in query_lower:
        complexity_score += 2
    if query_lower.count("join") > 2:
        complexity_score += 2
    if query_lower.count("and") > 3 or query_lower.count("or") > 2:
        complexity_score += 1
    
    if complexity_score >= 5:
        return "very_complex"
    elif complexity_score >= 3:
        return "complex"
    elif complexity_score >= 1:
        return "moderate"
    else:
        return "standard"

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
            sql = result.get("generated_sql", "")
            
            # Analyze SQL complexity
            sql_lower = sql.lower() if sql else ""
            has_join = "join" in sql_lower
            has_subquery = "select" in sql_lower and sql_lower.count("select") > 1
            has_aggregation = any(func in sql_lower for func in ["count", "sum", "avg", "max", "min"])
            has_groupby = "group by" in sql_lower
            has_window = "over" in sql_lower
            
            return {
                "success": True,
                "response_time": (end_time - start_time) * 1000,
                "sql": sql,
                "sql_length": len(sql) if sql else 0,
                "has_join": has_join,
                "has_subquery": has_subquery,
                "has_aggregation": has_aggregation,
                "has_groupby": has_groupby,
                "has_window": has_window,
                "method": result.get("metadata", {}).get("method", "unknown"),
                "error": None
            }
        else:
            return {
                "success": False,
                "response_time": (end_time - start_time) * 1000,
                "sql": None,
                "sql_length": 0,
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "response_time": 0,
            "sql": None,
            "sql_length": 0,
            "error": str(e)
        }

def run_complex_test():
    """Run the complex query performance test"""
    print("=" * 80)
    print("COMPLEX SQL QUERY PERFORMANCE TEST")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Generate queries
    print("Generating 200 technically complex queries...")
    queries = generate_complex_queries()
    
    # Count complexity levels
    complexity_counts = {}
    for q in queries:
        level = q["complexity"]
        complexity_counts[level] = complexity_counts.get(level, 0) + 1
    
    print(f"✓ Generated {len(queries)} complex queries")
    print(f"  Complexity distribution:")
    for level, count in sorted(complexity_counts.items()):
        print(f"    - {level}: {count} queries")
    print()
    
    # Execute queries
    results = []
    success_count = 0
    response_times = []
    sql_features = {
        "joins": 0,
        "subqueries": 0,
        "aggregations": 0,
        "groupby": 0,
        "windows": 0
    }
    
    print("Executing complex queries...")
    print("-" * 80)
    
    for i, query_obj in enumerate(queries, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(queries)} ({i/len(queries)*100:.1f}%)")
        
        result = execute_query(query_obj["query"])
        
        results.append({
            "id": query_obj["id"],
            "query": query_obj["query"],
            "complexity": query_obj["complexity"],
            **result
        })
        
        if result["success"]:
            success_count += 1
            response_times.append(result["response_time"])
            
            # Track SQL features
            if result.get("has_join"):
                sql_features["joins"] += 1
            if result.get("has_subquery"):
                sql_features["subqueries"] += 1
            if result.get("has_aggregation"):
                sql_features["aggregations"] += 1
            if result.get("has_groupby"):
                sql_features["groupby"] += 1
            if result.get("has_window"):
                sql_features["windows"] += 1
    
    print(f"Progress: {len(queries)}/{len(queries)} (100%)")
    print()
    
    # Analysis
    print("=" * 80)
    print("COMPLEX QUERY ANALYSIS")
    print("=" * 80)
    print()
    
    print("Overall Results:")
    print(f"  Total Queries: {len(queries)}")
    print(f"  Successful: {success_count} ({success_count/len(queries)*100:.1f}%)")
    print(f"  Failed: {len(queries)-success_count} ({(len(queries)-success_count)/len(queries)*100:.1f}%)")
    print()
    
    if response_times:
        print("Response Time Statistics (ms):")
        print(f"  Min: {min(response_times):.2f}")
        print(f"  Max: {max(response_times):.2f}")
        print(f"  Mean: {statistics.mean(response_times):.2f}")
        print(f"  Median: {statistics.median(response_times):.2f}")
        if len(response_times) > 1:
            print(f"  Std Dev: {statistics.stdev(response_times):.2f}")
        print()
        
        # Complexity analysis
        print("Performance by Complexity Level:")
        complexity_perf = {}
        for r in results:
            level = r["complexity"]
            if level not in complexity_perf:
                complexity_perf[level] = {"times": [], "success": 0, "total": 0}
            complexity_perf[level]["total"] += 1
            if r["success"]:
                complexity_perf[level]["success"] += 1
                complexity_perf[level]["times"].append(r["response_time"])
        
        print(f"{'Level':<15} {'Success Rate':<15} {'Avg Time (ms)':<15} {'Queries':<10}")
        print("-" * 55)
        for level in ["standard", "moderate", "complex", "very_complex"]:
            if level in complexity_perf:
                perf = complexity_perf[level]
                success_rate = (perf["success"] / perf["total"] * 100) if perf["total"] > 0 else 0
                avg_time = statistics.mean(perf["times"]) if perf["times"] else 0
                print(f"{level:<15} {success_rate:<15.1f}% {avg_time:<15.0f} {perf['total']:<10}")
        print()
        
        print("SQL Features Generated:")
        print(f"  Queries with JOINs: {sql_features['joins']} ({sql_features['joins']/success_count*100:.1f}%)")
        print(f"  Queries with Subqueries: {sql_features['subqueries']} ({sql_features['subqueries']/success_count*100:.1f}%)")
        print(f"  Queries with Aggregations: {sql_features['aggregations']} ({sql_features['aggregations']/success_count*100:.1f}%)")
        print(f"  Queries with GROUP BY: {sql_features['groupby']} ({sql_features['groupby']/success_count*100:.1f}%)")
        print(f"  Queries with Window Functions: {sql_features['windows']} ({sql_features['windows']/success_count*100:.1f}%)")
        print()
        
        # SQL length analysis
        sql_lengths = [r["sql_length"] for r in results if r["success"] and r["sql_length"] > 0]
        if sql_lengths:
            print("Generated SQL Complexity:")
            print(f"  Shortest SQL: {min(sql_lengths)} characters")
            print(f"  Longest SQL: {max(sql_lengths)} characters")
            print(f"  Average SQL Length: {statistics.mean(sql_lengths):.0f} characters")
    
    # Show examples of complex queries
    complex_success = [r for r in results if r["complexity"] == "very_complex" and r["success"]]
    if complex_success:
        print()
        print("Sample Very Complex Queries (Successfully Generated):")
        print("-" * 80)
        for r in complex_success[:3]:
            print(f"Query: {r['query'][:70]}...")
            if r["sql"]:
                sql_preview = r["sql"][:150].replace("\n", " ")
                print(f"SQL: {sql_preview}...")
            print(f"Time: {r['response_time']:.0f}ms")
            print()
    
    # Save results
    with open("complex_query_results.json", "w") as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "summary": {
                "total": len(queries),
                "success": success_count,
                "success_rate": success_count/len(queries)*100,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "sql_features": sql_features,
                "complexity_distribution": complexity_counts
            },
            "results": results
        }, f, indent=2)
    
    print("=" * 80)
    print("TEST COMPLETED")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Results saved to: complex_query_results.json")
    print("=" * 80)

if __name__ == "__main__":
    run_complex_test()