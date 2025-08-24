#!/usr/bin/env python3
"""Test to see which application statuses have data"""

import requests

BASE_URL = "http://localhost:8000/api"

# First, let's see what statuses exist in the data
query = "SELECT Status, COUNT(*) as Count FROM ScholarshipApplications GROUP BY Status ORDER BY Status"

response = requests.post(
    f"{BASE_URL}/queries/execute",
    json={
        "connection_id": 1,
        "prompt": query
    }
)

if response.status_code == 200:
    result = response.json()
    print("Application Status Distribution:")
    print("=" * 40)
    
    if 'result_data' in result:
        if isinstance(result['result_data'], dict) and 'data' in result['result_data']:
            data = result['result_data']['data']
            
            status_names = {
                1: "PENDING/DRAFT",
                2: "SUBMITTED",
                3: "UNDER REVIEW",
                4: "APPROVED",
                5: "REJECTED",
                6: "CANCELLED"
            }
            
            for row in data:
                status = row.get('Status')
                count = row.get('Count')
                name = status_names.get(status, f"UNKNOWN ({status})")
                print(f"Status {status} ({name}): {count} applications")
                
            print("\n" + "=" * 40)
            print("Total applications:", sum(row['Count'] for row in data))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
