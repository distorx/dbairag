#!/usr/bin/env python3
"""
Test script to verify that 'show cities' query uses pattern matching
instead of expensive LLM calls
"""

import asyncio
import time
import aiohttp
import json

async def test_show_cities():
    """Test the 'show cities' query performance"""
    
    # API endpoint
    url = "http://localhost:8000/api/queries/execute"
    
    # Test query - should match our new pattern
    test_queries = [
        "show cities",
        "show city",
        "list cities",
        "show students",
        "display cities",
        "view cities"
    ]
    
    headers = {
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Testing query: '{query}'")
            print(f"{'='*60}")
            
            data = {
                "connection_id": "1",  # Assuming connection ID 1 exists
                "prompt": query
            }
            
            start_time = time.time()
            
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        elapsed_time = time.time() - start_time
                        
                        print(f"✅ Success! Time: {elapsed_time:.2f} seconds")
                        print(f"SQL Generated: {result.get('sql', 'N/A')[:200]}")
                        
                        # Check if it was pattern matched (should be fast)
                        if elapsed_time < 2.0:
                            print(f"🚀 FAST! Used pattern matching (avoided LLM)")
                        else:
                            print(f"⚠️  SLOW! Likely used LLM generation")
                            
                        # Check metadata
                        metadata = result.get('metadata', {})
                        if metadata.get('pattern_matched'):
                            print(f"✅ Confirmed: Pattern matching was used")
                        
                        # Show result count
                        if result.get('data'):
                            print(f"Rows returned: {len(result['data'])}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Error {response.status}: {error_text}")
                        
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
                print("Make sure the backend is running and a connection exists")

if __name__ == "__main__":
    print("Testing 'show cities' query performance...")
    print("This should now use pattern matching instead of LLM")
    asyncio.run(test_show_cities())