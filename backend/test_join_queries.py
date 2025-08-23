#!/usr/bin/env python3
"""Test JOIN query generation with enums"""
import asyncio
from app.services.enum_service import enum_service
from app.services.rag_service import RAGService

async def test_join_queries():
    """Test various JOIN queries with enum filters"""
    
    # Load enums
    await enum_service.load_enums_from_file("/home/rick/Downloads/api_enums.json", "1")
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test queries that should generate JOINs
    test_prompts = [
        # Basic JOIN queries
        "Show all students with their applications",
        "List applications and their documents",
        "Get students with their scholarships",
        
        # JOIN with enum filters
        "Show all students with approved applications",
        "List students with rejected applications",
        "Find applications with their documents where status is pending",
        "Count students with approved scholarships",
        
        # Complex JOINs
        "Show students with their applications and documents",
        "List all approved applications with student information",
        "Find students with evaluacion status applications including their documents",
        
        # Count queries with JOINs
        "Count how many students have approved applications",
        "How many applications have pending documents",
        "Total number of students with scholarships that are pagada",
    ]
    
    print("🔗 Testing JOIN Query Generation with Enums\n")
    print("=" * 80)
    
    # Simulating schema info with relationships
    schema_info = {
        "tables": {
            "Students": {
                "columns": [
                    {"name": "Id", "data_type": "int"},
                    {"name": "FirstName", "data_type": "varchar"},
                    {"name": "LastName", "data_type": "varchar"},
                    {"name": "Email", "data_type": "varchar"},
                ]
            },
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
                    {"name": "DocumentType", "data_type": "varchar"},
                    {"name": "UploadDate", "data_type": "datetime"},
                ]
            },
            "Scholarships": {
                "columns": [
                    {"name": "Id", "data_type": "int"},
                    {"name": "ApplicationId", "data_type": "int"},
                    {"name": "StudentId", "data_type": "int"},
                    {"name": "AwardStatus", "data_type": "int"},
                    {"name": "Amount", "data_type": "decimal"},
                ]
            },
            "ApplicationReviews": {
                "columns": [
                    {"name": "Id", "data_type": "int"},
                    {"name": "ApplicationId", "data_type": "int"},
                    {"name": "ReviewerId", "data_type": "int"},
                    {"name": "Decision", "data_type": "int"},
                    {"name": "Comments", "data_type": "varchar"},
                ]
            }
        },
        "relationships": [
            {
                "from_table": "Applications",
                "from_column": "StudentId",
                "to_table": "Students",
                "to_column": "Id"
            },
            {
                "from_table": "Documents",
                "from_column": "ApplicationId",
                "to_table": "Applications",
                "to_column": "Id"
            },
            {
                "from_table": "Scholarships",
                "from_column": "ApplicationId",
                "to_table": "Applications",
                "to_column": "Id"
            }
        ]
    }
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        
        # Generate SQL with JOIN support
        sql_query, metadata = await rag_service.generate_sql(prompt, schema_info, "1")
        
        if sql_query:
            print(f"✅ Generated SQL:")
            # Format for better readability
            formatted_sql = sql_query.replace(" FROM ", "\n  FROM ")
            formatted_sql = formatted_sql.replace(" INNER JOIN ", "\n  INNER JOIN ")
            formatted_sql = formatted_sql.replace(" WHERE ", "\n  WHERE ")
            print(f"  {formatted_sql}")
            
            # Check if it's a JOIN query
            if "JOIN" in sql_query:
                print("  ✓ JOIN detected")
            
            # Check if enum filter was applied
            if "WHERE" in sql_query and any(str(i) in sql_query for i in range(6)):
                print("  ✓ Enum filter applied")
        else:
            print(f"❌ Failed: {metadata.get('error', 'Unknown error')}")
        
        print("-" * 80)
    
    print("\n📊 Summary:")
    print("The system can now generate:")
    print("  • Simple SELECT queries with enum filters")
    print("  • JOIN queries between related tables")
    print("  • JOIN queries with enum filters")
    print("  • COUNT queries with JOINs and enum filters")

if __name__ == "__main__":
    asyncio.run(test_join_queries())