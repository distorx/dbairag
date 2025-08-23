#!/usr/bin/env python3
"""
Comprehensive API Test Suite v2 - With better error handling and debugging
Tests fuzzy matching, relationship detection, and query processing
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

class APITestSuite:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.connection_id = 2  # Using SQLite test database
        self.results = []
        self.start_time = time.time()
        
    def execute_query(self, prompt: str) -> Tuple[bool, Any, float]:
        """Execute a single query and return results"""
        url = f"{self.base_url}/api/queries/execute"
        data = {
            "prompt": prompt,
            "connection_id": self.connection_id
        }
        
        start = time.time()
        try:
            response = requests.post(url, json=data, timeout=10)
            duration = time.time() - start
            
            if response.status_code == 200:
                return True, response.json(), duration
            else:
                return False, f"HTTP {response.status_code}: {response.text[:200]}", duration
        except requests.exceptions.Timeout:
            duration = time.time() - start
            return False, "Timeout after 10 seconds", duration
        except Exception as e:
            duration = time.time() - start
            return False, str(e), duration
    
    def run_test_category(self, category: str, queries: List[str]):
        """Run a category of tests"""
        print(f"\n{'='*60}")
        print(f"{category}")
        print('='*60)
        
        success = 0
        failed = 0
        
        for query in queries:
            success_flag, result, duration = self.execute_query(query)
            
            if success_flag:
                success += 1
                status = "✅"
                # Extract row count if available
                if isinstance(result, dict) and "result_data" in result:
                    data = result.get("result_data")
                    if isinstance(data, dict) and "row_count" in data:
                        detail = f"{data['row_count']} rows"
                    elif isinstance(data, str):
                        detail = data[:50]
                    else:
                        detail = "Success"
                else:
                    detail = "Success"
            else:
                failed += 1
                status = "❌"
                detail = str(result)[:100]
            
            print(f"{status} '{query[:40]}...' - {duration:.2f}s - {detail}")
            
            self.results.append({
                "category": category,
                "query": query,
                "success": success_flag,
                "duration": duration,
                "result": result
            })
        
        print(f"\nCategory Summary: {success} passed, {failed} failed")
        return success, failed
    
    def run_all_tests(self):
        """Run all test categories"""
        print("🚀 Starting Comprehensive API Test Suite")
        print(f"   Using connection ID: {self.connection_id}")
        print(f"   API URL: {self.base_url}")
        
        total_success = 0
        total_failed = 0
        
        # Test 1: Basic Queries
        queries = [
            "show tables",
            "count students",
            "list students",
            "show all students"
        ]
        s, f = self.run_test_category("BASIC QUERIES", queries)
        total_success += s
        total_failed += f
        
        # Test 2: Fuzzy Matching (Misspellings)
        queries = [
            "count studnts",  # Missing 'e'
            "count studens",  # Missing 't'
            "count student",  # Singular
            "show studnt",    # Missing 'e'
        ]
        s, f = self.run_test_category("FUZZY MATCHING (MISSPELLINGS)", queries)
        total_success += s
        total_failed += f
        
        # Test 3: Soundex Matching
        queries = [
            "count stewdents",  # Phonetically similar
            "show stoodents",   # Phonetically similar
        ]
        s, f = self.run_test_category("SOUNDEX MATCHING", queries)
        total_success += s
        total_failed += f
        
        # Test 4: Relationship Detection
        queries = [
            "count students with cars",
            "show students with applications",
            "list students with courses"
        ]
        s, f = self.run_test_category("RELATIONSHIP DETECTION", queries)
        total_success += s
        total_failed += f
        
        # Test 5: Case Variations
        queries = [
            "COUNT STUDENTS",
            "Count Students",
            "count STUDENTS",
            "CoUnT sTuDeNtS"
        ]
        s, f = self.run_test_category("CASE VARIATIONS", queries)
        total_success += s
        total_failed += f
        
        # Test 6: Complex Queries
        queries = [
            "total students",
            "number of students",
            "how many students"
        ]
        s, f = self.run_test_category("COMPLEX QUERIES", queries)
        total_success += s
        total_failed += f
        
        # Generate Report
        self.generate_report(total_success, total_failed)
    
    def generate_report(self, total_success: int, total_failed: int):
        """Generate test report"""
        total_tests = total_success + total_failed
        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        total_time = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("📊 TEST REPORT")
        print("="*80)
        
        print(f"\n✅ Total Tests: {total_tests}")
        print(f"   Passed: {total_success} ({total_success/total_tests*100:.1f}%)")
        print(f"   Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Time: {total_time:.1f}s")
        
        # Category breakdown
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"success": 0, "failed": 0}
            if result["success"]:
                categories[cat]["success"] += 1
            else:
                categories[cat]["failed"] += 1
        
        print("\n📈 BY CATEGORY:")
        for cat, stats in categories.items():
            total = stats["success"] + stats["failed"]
            rate = (stats["success"] / total * 100) if total > 0 else 0
            print(f"   {cat}: {rate:.1f}% success ({stats['success']}/{total})")
        
        # Find slowest queries
        slowest = sorted(self.results, key=lambda x: x["duration"], reverse=True)[:3]
        print("\n⏱️  SLOWEST QUERIES:")
        for r in slowest:
            print(f"   '{r['query'][:30]}...' - {r['duration']:.2f}s")
        
        # Key findings
        print("\n🔍 KEY FINDINGS:")
        
        # Check fuzzy matching
        fuzzy_results = [r for r in self.results if "FUZZY" in r["category"] or "SOUNDEX" in r["category"]]
        fuzzy_success = sum(1 for r in fuzzy_results if r["success"])
        if fuzzy_results:
            fuzzy_rate = (fuzzy_success / len(fuzzy_results)) * 100
            print(f"   • Fuzzy Matching Success Rate: {fuzzy_rate:.1f}%")
            if fuzzy_rate >= 75:
                print("     ✅ Fuzzy matching working well!")
            else:
                print("     ⚠️ Fuzzy matching needs improvement")
        
        # Check relationship detection
        rel_results = [r for r in self.results if "RELATIONSHIP" in r["category"]]
        rel_success = sum(1 for r in rel_results if r["success"])
        if rel_results:
            rel_rate = (rel_success / len(rel_results)) * 100
            print(f"   • Relationship Detection Rate: {rel_rate:.1f}%")
            if rel_rate >= 75:
                print("     ✅ Relationship detection working!")
            else:
                print("     ⚠️ Relationship detection needs work")
        
        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": total_success,
                    "failed": total_failed,
                    "success_rate": success_rate,
                    "total_time": total_time
                },
                "categories": categories,
                "results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Final verdict
        print("\n" + "="*80)
        if success_rate >= 80:
            print("✅ TEST SUITE PASSED")
        elif success_rate >= 60:
            print("⚠️ TEST SUITE PARTIALLY PASSED")
        else:
            print("❌ TEST SUITE FAILED")
        print(f"Overall Success Rate: {success_rate:.1f}%")
        print("="*80)

if __name__ == "__main__":
    tester = APITestSuite()
    tester.run_all_tests()