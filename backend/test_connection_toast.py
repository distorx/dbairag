#!/usr/bin/env python3
"""Test script to create and test a connection"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_connection_flow():
    """Test creating and testing a connection"""
    
    print("🧪 Testing Connection Flow with Toast Notifications\n")
    print("=" * 60)
    
    # 1. Create a test connection
    print("\n1️⃣ Creating a new connection...")
    connection_data = {
        "name": "Test Database",
        "connection_string": "Server=localhost;Database=TestDB;User Id=sa;Password=YourPassword123;",
        "database_type": "mssql",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/api/connections", json=connection_data)
    
    if response.status_code == 200:
        connection = response.json()
        print(f"✅ Connection created with ID: {connection['id']}")
        print(f"   Name: {connection['name']}")
        
        # 2. Test the connection
        print(f"\n2️⃣ Testing connection ID {connection['id']}...")
        test_response = requests.post(f"{BASE_URL}/api/connections/{connection['id']}/test")
        
        if test_response.status_code == 200:
            result = test_response.json()
            if result['success']:
                print(f"✅ Connection test successful!")
                print(f"   Message: {result['message']}")
            else:
                print(f"❌ Connection test failed")
                print(f"   Message: {result['message']}")
        else:
            print(f"❌ Failed to test connection: {test_response.status_code}")
        
        # 3. Load enums for the connection
        print(f"\n3️⃣ Loading enums for connection...")
        enum_data = {
            "file_path": "/home/rick/Downloads/api_enums.json"
        }
        enum_response = requests.post(
            f"{BASE_URL}/api/queries/enums/{connection['id']}/load",
            json=enum_data
        )
        
        if enum_response.status_code == 200:
            print(f"✅ Enums loaded successfully")
        else:
            print(f"⚠️ Failed to load enums: {enum_response.status_code}")
        
        # 4. Get schema information
        print(f"\n4️⃣ Getting schema information...")
        schema_response = requests.get(f"{BASE_URL}/api/queries/schema/{connection['id']}")
        
        if schema_response.status_code == 200:
            schema = schema_response.json()
            print(f"✅ Schema retrieved")
            print(f"   Tables: {len(schema.get('tables', []))}")
            if schema.get('tables'):
                for table in schema['tables'][:3]:  # Show first 3 tables
                    print(f"   - {table['name']} ({table['row_count']} rows)")
        else:
            print(f"⚠️ Failed to get schema: {schema_response.status_code}")
        
        # 5. Clean up - delete the test connection
        print(f"\n5️⃣ Cleaning up...")
        delete_response = requests.delete(f"{BASE_URL}/api/connections/{connection['id']}")
        
        if delete_response.status_code == 200:
            print(f"✅ Test connection deleted")
        else:
            print(f"⚠️ Failed to delete connection: {delete_response.status_code}")
    else:
        print(f"❌ Failed to create connection: {response.status_code}")
        if response.text:
            print(f"   Error: {response.text}")
    
    print("\n" + "=" * 60)
    print("\n📋 Toast Notifications Expected:")
    print("  • 'Connection saved successfully!' when connection is created")
    print("  • 'Testing connection...' when test starts")
    print("  • 'Connection test successful!' or error message")
    print("  • 'Connection deleted successfully' when deleted")
    print("\n🌐 Open http://localhost:4200 in your browser to see the toast notifications!")

if __name__ == "__main__":
    test_connection_flow()