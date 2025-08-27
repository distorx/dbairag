#!/usr/bin/env python3
"""
Detailed performance breakdown test for simple queries
"""

import asyncio
import time
import aiohttp
import json

async def test_performance_breakdown():
    """Test with detailed timing breakdown"""
    
    url = "http://localhost:8000/api/queries/execute"
    query = "show cities"
    
    headers = {"Content-Type": "application/json"}
    data = {"connection_id": "1", "prompt": query}
    
    async with aiohttp.ClientSession() as session:
        print(f"Testing query: '{query}'")
        print("="*60)
        
        # Test multiple times to see if there's caching
        for i in range(5):
            print(f"\nRun #{i+1}:")
            
            start_time = time.time()
            
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        total_time = time.time() - start_time
                        
                        print(f"  HTTP Response Time: {response_time*1000:.0f}ms")
                        print(f"  Total Time (with parsing): {total_time*1000:.0f}ms")
                        
                        # Check execution time from server
                        server_time = result.get('execution_time', 'N/A')
                        print(f"  Server Reported Time: {server_time}ms")
                        
                        # Check metadata
                        metadata = result.get('metadata', {})
                        if metadata.get('execution_time_ms'):
                            print(f"  SQL Generation Time: {metadata['execution_time_ms']:.0f}ms")
                        
                        # Check if cached
                        if metadata.get('cached'):
                            print(f"  ✅ Result was cached")
                        elif metadata.get('pattern_matched'):
                            print(f"  ✅ Pattern matching used")
                        
                        # Show data size
                        result_data = result.get('result_data', {})
                        if isinstance(result_data, dict):
                            row_count = result_data.get('row_count', 0)
                            print(f"  Rows returned: {row_count}")
                            
                            # Calculate JSON size
                            json_size = len(json.dumps(result_data))
                            print(f"  Response size: {json_size/1024:.1f}KB")
                        
                    else:
                        print(f"❌ Error {response.status}")
                        
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
            
            # Small delay between requests
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    print("Performance Breakdown Test")
    print("Expected: <100ms for cached/pattern matched queries")
    print()
    asyncio.run(test_performance_breakdown())