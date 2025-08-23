#!/usr/bin/env python3
"""Script to load enums for connections"""
import asyncio
import json
from pathlib import Path
from app.services.enum_service import enum_service

async def load_default_enums():
    """Load default enums for testing"""
    
    # Check if the api_enums.json file exists
    enum_file = Path("/home/rick/Downloads/api_enums.json")
    
    if enum_file.exists():
        # Load for connection ID 1 (assuming this is the default test connection)
        success = await enum_service.load_enums_from_file(str(enum_file), "1")
        if success:
            print(f"✅ Loaded enums from {enum_file} for connection 1")
            
            # Show loaded enums
            suggestions = enum_service.get_enum_suggestions("1")
            print(f"📊 Loaded {len(suggestions)} enum types:")
            for enum_name in suggestions.keys():
                print(f"  - {enum_name}")
        else:
            print(f"❌ Failed to load enums from {enum_file}")
    else:
        print(f"⚠️ Enum file not found: {enum_file}")

if __name__ == "__main__":
    asyncio.run(load_default_enums())