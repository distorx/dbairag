#!/usr/bin/env python3
"""
Extensive MSSQL Connection Test Suite
Tests 100+ scenarios with retry logic and comprehensive reporting
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import random
import string

class MSSQLTestSuite:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.connection_id = 2  # Use SQLite test database (connection 2)
        self.results = []
        self.test_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.retry_count = 0
        self.total_retries = 0
        
    async def execute_query(self, query: str, max_retries: int = 3) -> Tuple[bool, Any, str]:
        """Execute a query against the API with retry logic"""
        url = f"{self.api_url}/api/queries/execute"
        headers = {"Content-Type": "application/json"}
        data = {
            "prompt": query,  # API expects 'prompt' not 'query'
            "connection_id": self.connection_id
        }
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            result = await response.json()
                            return True, result, "Success"
                        else:
                            error_text = await response.text()
                            if attempt < max_retries - 1:
                                self.total_retries += 1
                                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                                continue
                            return False, None, f"HTTP {response.status}: {error_text}"
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    self.total_retries += 1
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                return False, None, "Query timeout after 15 seconds"
            except Exception as e:
                if attempt < max_retries - 1:
                    self.total_retries += 1
                    await asyncio.sleep(1)
                    continue
                return False, None, f"Exception: {str(e)}"
        
        return False, None, "Max retries exceeded"
    
    async def test_basic_queries(self):
        """Test basic SQL queries"""
        print("\n" + "="*60)
        print("TESTING BASIC QUERIES")
        print("="*60)
        
        basic_queries = [
            "show tables",
            "show databases",
            "count students",
            "count applications",
            "list students",
            "show all applications",
            "total students",
            "number of applications",
        ]
        
        for query in basic_queries:
            await self.run_test(query, "Basic Query")
    
    async def test_fuzzy_matching(self):
        """Test fuzzy matching with misspelled table names"""
        print("\n" + "="*60)
        print("TESTING FUZZY MATCHING (MISSPELLED NAMES)")
        print("="*60)
        
        # Common misspellings and variations
        fuzzy_queries = [
            "count studnts",  # Missing 'e'
            "count studens",  # Missing 't'
            "count student",  # Singular vs plural
            "count applicatons",  # Missing 'i'
            "count aplications",  # Missing 'p'
            "show citys",  # Wrong plural
            "show city",  # Singular
            "count scholarhip",  # Missing 's'
            "count scholarshp",  # Missing 'i'
            "show highschols",  # Missing 'o'
            "show high schools",  # Space variation
            "count documets",  # Missing 'n'
            "show studet",  # Multiple errors
            "count aplication",  # Multiple errors
        ]
        
        for query in fuzzy_queries:
            await self.run_test(query, "Fuzzy Matching")
    
    async def test_soundex_matching(self):
        """Test soundex phonetic matching"""
        print("\n" + "="*60)
        print("TESTING SOUNDEX MATCHING (PHONETIC)")
        print("="*60)
        
        soundex_queries = [
            "count stewdents",  # Phonetically similar
            "count aplikayshuns",  # Phonetic spelling
            "show sitees",  # Phonetic spelling
            "count skolarships",  # Phonetic spelling
            "show hi skools",  # Phonetic spelling
            "count dokuments",  # Phonetic spelling
        ]
        
        for query in soundex_queries:
            await self.run_test(query, "Soundex Matching")
    
    async def test_relationship_queries(self):
        """Test relationship/junction table detection"""
        print("\n" + "="*60)
        print("TESTING RELATIONSHIP TABLE DETECTION")
        print("="*60)
        
        relationship_queries = [
            "count students with applications",
            "count student with application",
            "show students with documents",
            "list students with scholarships",
            "count applications with documents",
            "show students with their applications",
            "list students and their documents",
            "count students including applications",
            "show students along with documents",
        ]
        
        for query in relationship_queries:
            await self.run_test(query, "Relationship Detection")
    
    async def test_complex_queries(self):
        """Test complex query patterns"""
        print("\n" + "="*60)
        print("TESTING COMPLEX QUERIES")
        print("="*60)
        
        complex_queries = [
            "average scholarship amount",
            "max application score",
            "min student age",
            "sum of all scholarships",
            "count approved applications",
            "count rejected applications",
            "count pending applications",
            "show approved students",
            "list rejected applications",
        ]
        
        for query in complex_queries:
            await self.run_test(query, "Complex Query")
    
    async def test_case_variations(self):
        """Test case sensitivity handling"""
        print("\n" + "="*60)
        print("TESTING CASE VARIATIONS")
        print("="*60)
        
        case_queries = [
            "COUNT STUDENTS",
            "Count Students",
            "count STUDENTS",
            "CoUnT sTuDeNtS",
            "SHOW APPLICATIONS",
            "Show Applications",
            "show APPLICATIONS",
        ]
        
        for query in case_queries:
            await self.run_test(query, "Case Variation")
    
    async def test_empty_vs_populated_tables(self):
        """Test preference for populated tables over empty ones"""
        print("\n" + "="*60)
        print("TESTING EMPTY VS POPULATED TABLE PREFERENCE")
        print("="*60)
        
        # These should prefer tables with data
        preference_queries = [
            "count city",  # Should prefer Cities with data over City if empty
            "show city",
            "list city",
            "count cities",
            "show all cities",
        ]
        
        for query in preference_queries:
            await self.run_test(query, "Table Preference")
    
    async def test_compound_words(self):
        """Test compound word handling"""
        print("\n" + "="*60)
        print("TESTING COMPOUND WORD HANDLING")
        print("="*60)
        
        compound_queries = [
            "count highschools",  # One word vs HighSchools
            "count high schools",  # Two words
            "show highschool",
            "list high school",
            "count studentdocuments",  # Compound
            "show student documents",  # Separated
        ]
        
        for query in compound_queries:
            await self.run_test(query, "Compound Words")
    
    async def test_partial_matches(self):
        """Test partial table name matches"""
        print("\n" + "="*60)
        print("TESTING PARTIAL MATCHES")
        print("="*60)
        
        partial_queries = [
            "count stud",  # Partial: students
            "show app",  # Partial: applications
            "list doc",  # Partial: documents
            "count schol",  # Partial: scholarships
            "show high",  # Partial: highschools
        ]
        
        for query in partial_queries:
            await self.run_test(query, "Partial Match")
    
    async def test_stress_scenarios(self):
        """Test stress scenarios with rapid queries"""
        print("\n" + "="*60)
        print("TESTING STRESS SCENARIOS")
        print("="*60)
        
        stress_queries = []
        tables = ["students", "applications", "documents", "scholarships", "cities", "highschools"]
        operations = ["count", "show", "list", "total", "number of"]
        
        # Generate 20 random queries for stress testing
        for _ in range(20):
            operation = random.choice(operations)
            table = random.choice(tables)
            # Randomly introduce typos
            if random.random() > 0.5:
                # Introduce a typo
                pos = random.randint(0, len(table)-1)
                table = table[:pos] + random.choice(string.ascii_lowercase) + table[pos+1:]
            
            query = f"{operation} {table}"
            stress_queries.append(query)
        
        # Execute in parallel batches
        batch_size = 5
        for i in range(0, len(stress_queries), batch_size):
            batch = stress_queries[i:i+batch_size]
            tasks = [self.run_test(query, "Stress Test", silent=True) for query in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.5)  # Small delay between batches
    
    async def test_edge_cases(self):
        """Test edge cases and unusual queries"""
        print("\n" + "="*60)
        print("TESTING EDGE CASES")
        print("="*60)
        
        edge_queries = [
            "",  # Empty query
            "   ",  # Whitespace only
            "count",  # Operation without table
            "students",  # Table without operation
            "count students applications",  # Multiple tables
            "show students; DROP TABLE students",  # SQL injection attempt
            "count students WHERE 1=1",  # Partial SQL
            "SELECT * FROM students",  # Full SQL
            "count students" * 10,  # Very long query
            "count 学生",  # Unicode characters
            "count students🎓",  # Emoji
            "count NULL",  # NULL value
            "count students\nwith applications",  # Newline
            "count\tstudents",  # Tab character
        ]
        
        for query in edge_queries:
            await self.run_test(query, "Edge Case")
    
    async def run_test(self, query: str, category: str, silent: bool = False):
        """Run a single test and record results"""
        self.test_count += 1
        
        if not silent:
            print(f"\nTest {self.test_count}: {query[:50]}...")
        
        start_time = time.time()
        success, result, error_msg = await self.execute_query(query)
        duration = time.time() - start_time
        
        if success:
            self.success_count += 1
            status = "✅ SUCCESS"
            if not silent:
                # Try to extract result count or first few rows
                if isinstance(result, dict):
                    if "data" in result and result["data"]:
                        if isinstance(result["data"], list):
                            print(f"  {status} - {len(result['data'])} rows returned ({duration:.2f}s)")
                        else:
                            print(f"  {status} - Result: {str(result['data'])[:100]} ({duration:.2f}s)")
                    else:
                        print(f"  {status} - Empty result ({duration:.2f}s)")
                else:
                    print(f"  {status} ({duration:.2f}s)")
        else:
            self.failure_count += 1
            status = "❌ FAILED"
            if not silent:
                print(f"  {status} - {error_msg} ({duration:.2f}s)")
        
        self.results.append({
            "test_number": self.test_count,
            "category": category,
            "query": query,
            "success": success,
            "duration": duration,
            "error": error_msg if not success else None,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"  Total Tests Run: {self.test_count}")
        print(f"  Successful: {self.success_count} ({self.success_count/self.test_count*100:.1f}%)")
        print(f"  Failed: {self.failure_count} ({self.failure_count/self.test_count*100:.1f}%)")
        print(f"  Total Retries: {self.total_retries}")
        print(f"  Average Retries per Test: {self.total_retries/self.test_count:.2f}")
        
        # Group results by category
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"success": 0, "failure": 0, "tests": []}
            
            if result["success"]:
                categories[cat]["success"] += 1
            else:
                categories[cat]["failure"] += 1
            categories[cat]["tests"].append(result)
        
        print(f"\n📈 RESULTS BY CATEGORY:")
        for cat, data in categories.items():
            total = data["success"] + data["failure"]
            success_rate = (data["success"] / total * 100) if total > 0 else 0
            print(f"\n  {cat}:")
            print(f"    Tests: {total}")
            print(f"    Success Rate: {success_rate:.1f}%")
            print(f"    Successes: {data['success']}")
            print(f"    Failures: {data['failure']}")
            
            # Show failed tests in this category
            failed_tests = [t for t in data["tests"] if not t["success"]]
            if failed_tests:
                print(f"    Failed Queries:")
                for test in failed_tests[:5]:  # Show first 5 failures
                    print(f"      - '{test['query']}': {test['error']}")
        
        # Performance analysis
        durations = [r["duration"] for r in self.results]
        print(f"\n⏱️  PERFORMANCE METRICS:")
        print(f"  Average Query Time: {sum(durations)/len(durations):.3f}s")
        print(f"  Min Query Time: {min(durations):.3f}s")
        print(f"  Max Query Time: {max(durations):.3f}s")
        
        # Find slowest queries
        slowest = sorted(self.results, key=lambda x: x["duration"], reverse=True)[:5]
        print(f"\n  Slowest Queries:")
        for test in slowest:
            print(f"    - '{test['query']}': {test['duration']:.3f}s")
        
        # Error analysis
        errors = {}
        for result in self.results:
            if not result["success"] and result["error"]:
                error_type = result["error"].split(":")[0]
                if error_type not in errors:
                    errors[error_type] = 0
                errors[error_type] += 1
        
        if errors:
            print(f"\n⚠️  ERROR ANALYSIS:")
            for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error_type}: {count} occurrences")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.failure_count > self.test_count * 0.2:
            print("  ⚠️ High failure rate detected (>20%). Consider:")
            print("    - Checking database connection stability")
            print("    - Reviewing schema synchronization")
            print("    - Increasing timeout values")
        
        if self.total_retries > self.test_count * 0.5:
            print("  ⚠️ High retry rate detected. Consider:")
            print("    - Optimizing query processing")
            print("    - Caching frequently accessed schemas")
            print("    - Implementing connection pooling")
        
        if max(durations) > 10:
            print("  ⚠️ Slow queries detected (>10s). Consider:")
            print("    - Implementing query result caching")
            print("    - Optimizing fuzzy matching algorithms")
            print("    - Adding database indexes")
        
        # Save detailed report to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.test_count,
                    "success_count": self.success_count,
                    "failure_count": self.failure_count,
                    "success_rate": self.success_count/self.test_count*100,
                    "total_retries": self.total_retries,
                    "avg_duration": sum(durations)/len(durations)
                },
                "categories": categories,
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return self.success_count / self.test_count * 100  # Return success rate

async def main():
    print("🚀 Starting Extensive MSSQL Connection Test Suite")
    print("=" * 80)
    
    tester = MSSQLTestSuite()
    
    # Run all test categories
    await tester.test_basic_queries()
    await tester.test_fuzzy_matching()
    await tester.test_soundex_matching()
    await tester.test_relationship_queries()
    await tester.test_complex_queries()
    await tester.test_case_variations()
    await tester.test_empty_vs_populated_tables()
    await tester.test_compound_words()
    await tester.test_partial_matches()
    await tester.test_stress_scenarios()
    await tester.test_edge_cases()
    
    # Generate comprehensive report
    success_rate = tester.generate_report()
    
    print("\n" + "="*80)
    if success_rate >= 80:
        print("✅ TEST SUITE PASSED - Success rate: {:.1f}%".format(success_rate))
    elif success_rate >= 60:
        print("⚠️ TEST SUITE PARTIALLY PASSED - Success rate: {:.1f}%".format(success_rate))
    else:
        print("❌ TEST SUITE FAILED - Success rate: {:.1f}%".format(success_rate))
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())