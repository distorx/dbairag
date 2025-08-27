#!/usr/bin/env python3
"""
Test various limit queries
"""

import asyncio
import time
import aiohttp

async def test_limit_queries():
    """Test queries with different limits"""
    
    url = "http://localhost:8000/api/queries/execute"
    
    # Test various queries with limits
    queries = [
        "show 5 cities",
        "show 10 municipios",
        "list 3 students",
        "view 15 cities",
        "display 20 municipios",
        "show cities",  # No limit - should default to 100
    ]
    
    headers = {"Content-Type": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        for query in queries:
            print(f"\n{'='*60}")
            print(f"Query: '{query}'")
            
            data = {"connection_id": 1, "prompt": query}
            start_time = time.time()
            
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        elapsed_time = time.time() - start_time
                        
                        # Extract info
                        sql = result.get('generated_sql', 'N/A')
                        execution_time = result.get('execution_time', 'N/A')
                        row_count = result.get('result_data', {}).get('row_count', 0) if isinstance(result.get('result_data'), dict) else 0
                        
                        print(f"✅ Success in {elapsed_time:.2f}s (server: {execution_time}ms)")
                        print(f"   SQL: {sql}")
                        print(f"   Rows returned: {row_count}")
                        
                        if elapsed_time < 2.0:
                            print(f"   🚀 FAST - Pattern matching worked!")
                        else:
                            print(f"   ⚠️  SLOW - May have used LLM")
                    else:
                        print(f"❌ Error {response.status}")
                        
            except Exception as e:
                print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    print("Testing queries with different limits...")
    print("All should be fast (<2 seconds) with pattern matching")
    asyncio.run(test_limit_queries())