#!/usr/bin/env python3
"""Simple API test to verify it's working"""

import requests
import json

# Test the API with a simple query
url = "http://localhost:8000/api/queries/execute"
data = {
    "prompt": "show tables",
    "connection_id": 1
}

print("Testing API with simple query: 'show tables'")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Success! Response:")
        print(json.dumps(result, indent=2)[:500])  # Show first 500 chars
    else:
        print(f"Error: {response.text}")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 30 seconds")
except Exception as e:
    print(f"ERROR: {e}")