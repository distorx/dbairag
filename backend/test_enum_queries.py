#!/usr/bin/env python3
"""Test enum-aware SQL generation"""
import asyncio
from app.services.enum_service import enum_service
from app.services.rag_service import RAGService

async def test_enum_queries():
    """Test various enum-related queries"""
    
    # Load enums
    await enum_service.load_enums_from_file("/home/rick/Downloads/api_enums.json", "1")
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test queries
    test_prompts = [
        "Show all approved applications",
        "Count rejected applications",
        "Find pending documents",
        "Get all students with evaluacion status",
        "List applications with status aprobada",
        "Show scholarships that are pagada",
        "Find all rechazada applications",
    ]
    
    print("🧪 Testing Enum-Aware SQL Generation\n")
    print("=" * 60)
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        
        # Generate SQL (simulating schema info)
        schema_info = {
            "tables": {
                "Applications": {
                    "columns": [
                        {"name": "Id", "data_type": "int"},
                        {"name": "StudentId", "data_type": "int"},
                        {"name": "Status", "data_type": "int"},
                        {"name": "CreatedDate", "data_type": "datetime"},
                    ]
                },
                "Documents": {
                    "columns": [
                        {"name": "Id", "data_type": "int"},
                        {"name": "ApplicationId", "data_type": "int"},
                        {"name": "Status", "data_type": "int"},
                        {"name": "UploadDate", "data_type": "datetime"},
                    ]
                },
                "Scholarships": {
                    "columns": [
                        {"name": "Id", "data_type": "int"},
                        {"name": "ApplicationId", "data_type": "int"},
                        {"name": "AwardStatus", "data_type": "int"},
                        {"name": "Amount", "data_type": "decimal"},
                    ]
                }
            }
        }
        
        # Generate SQL with enum support
        sql_query, metadata = await rag_service.generate_sql(prompt, schema_info, "1")
        
        if sql_query:
            print(f"✅ Generated SQL: {sql_query}")
            
            # Apply enum translation
            translated_sql = enum_service.translate_enum_in_query(sql_query, "1")
            if translated_sql != sql_query:
                print(f"🔄 With Enum Translation: {translated_sql}")
        else:
            print(f"❌ Failed: {metadata.get('error', 'Unknown error')}")
        
        print("-" * 60)
    
    # Show enum context
    print("\n📚 Enum Context Available:")
    enum_context = enum_service.get_enum_context("1")
    if enum_context:
        lines = enum_context.split('\n')[:20]  # Show first 20 lines
        for line in lines:
            print(line)
        if len(enum_context.split('\n')) > 20:
            print("... (truncated)")

if __name__ == "__main__":
    asyncio.run(test_enum_queries())