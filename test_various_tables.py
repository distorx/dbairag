#!/usr/bin/env python3
"""
Test various "show [table]" queries to confirm pattern matching works
"""

import asyncio
import time
import aiohttp

async def test_table_queries():
    """Test various table queries"""
    
    url = "http://localhost:8000/api/queries/execute"
    
    # Various table queries - all should be fast now
    queries = [
        "show cities",
        "show students", 
        "show municipios",
        "list cities",
        "view students",
        "display cities",
        "show city",     # singular form
        "show municipio", # singular form
    ]
    
    headers = {"Content-Type": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        fast_count = 0
        slow_count = 0
        
        for query in queries:
            print(f"\n{'='*60}")
            print(f"Testing: '{query}'")
            
            data = {"connection_id": "1", "prompt": query}
            start_time = time.time()
            
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        elapsed_time = time.time() - start_time
                        
                        if elapsed_time < 2.0:
                            print(f"✅ FAST: {elapsed_time:.2f}s - Pattern matching worked!")
                            fast_count += 1
                        else:
                            print(f"⚠️  SLOW: {elapsed_time:.2f}s - Used LLM")
                            slow_count += 1
                            
                        # Show SQL
                        sql = result.get('generated_sql', 'N/A')
                        if sql and sql != 'N/A':
                            print(f"   SQL: {sql[:80]}...")
                    else:
                        print(f"❌ Error {response.status}")
                        
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"  Fast queries (pattern matched): {fast_count}")
        print(f"  Slow queries (LLM used): {slow_count}")
        print(f"  Success rate: {fast_count}/{len(queries)} ({100*fast_count/len(queries):.0f}%)")

if __name__ == "__main__":
    print("Testing various table queries with pattern matching...")
    print("All should be FAST (<2 seconds) if pattern matching is working")
    asyncio.run(test_table_queries())