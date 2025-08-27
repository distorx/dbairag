#!/usr/bin/env python3
"""
Test just the "show cities" query to verify pattern matching works
"""

import asyncio
import time
import aiohttp

async def test_single_query():
    """Test a single 'show cities' query"""
    
    url = "http://localhost:8000/api/queries/execute"
    query = "show cities"
    
    headers = {"Content-Type": "application/json"}
    data = {"connection_id": "1", "prompt": query}
    
    async with aiohttp.ClientSession() as session:
        print(f"Testing query: '{query}'")
        print("="*60)
        
        start_time = time.time()
        
        try:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    elapsed_time = time.time() - start_time
                    
                    print(f"✅ Success! Time: {elapsed_time:.2f} seconds")
                    
                    # Check if it was fast (pattern matched)
                    if elapsed_time < 2.0:
                        print(f"🚀 FAST! Pattern matching worked - avoided LLM")
                    else:
                        print(f"⚠️  SLOW! Used LLM generation")
                        print("This might be because it's loading the context for the first time")
                        print("Try running again to test if caching works")
                        
                    # Show SQL generated
                    sql = result.get('generated_sql', 'N/A')
                    if sql and sql != 'N/A':
                        print(f"SQL: {sql[:100]}...")
                        
                    # Show metadata
                    metadata = result.get('metadata', {})
                    if metadata.get('pattern_matched'):
                        print(f"✅ Metadata confirms: Pattern matching was used")
                    if metadata.get('fast_path'):
                        print(f"✅ Metadata confirms: Fast path was taken")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Error {response.status}: {error_text}")
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    print("Testing 'show cities' with pattern matching...")
    print("This should be FAST (<2 seconds) if pattern matching is working")
    print()
    asyncio.run(test_single_query())