#!/usr/bin/env python3
"""
Test script to demonstrate intelligent relationship table detection
"""

import asyncio
import sqlite3
from app.services.rag_service import RAGService
from app.services.schema_analyzer import SchemaAnalyzer
from sqlalchemy import create_engine

async def create_test_database():
    """Create a test database with relationship tables"""
    conn = sqlite3.connect('test_relationships.db')
    cursor = conn.cursor()
    
    # Create main entity tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            Id INTEGER PRIMARY KEY,
            Name TEXT,
            Email TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cars (
            Id INTEGER PRIMARY KEY,
            Make TEXT,
            Model TEXT,
            Year INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Courses (
            Id INTEGER PRIMARY KEY,
            Name TEXT,
            Credits INTEGER
        )
    ''')
    
    # Create relationship/junction tables with different naming patterns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS StudentCars (
            StudentId INTEGER,
            CarId INTEGER,
            AssignedDate TEXT,
            FOREIGN KEY (StudentId) REFERENCES Students(Id),
            FOREIGN KEY (CarId) REFERENCES Cars(Id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_courses (
            student_id INTEGER,
            course_id INTEGER,
            enrollment_date TEXT,
            grade TEXT,
            FOREIGN KEY (student_id) REFERENCES Students(Id),
            FOREIGN KEY (course_id) REFERENCES Courses(Id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ApplicationDocuments (
            ApplicationId INTEGER,
            DocumentId INTEGER,
            UploadDate TEXT
        )
    ''')
    
    # Insert sample data
    cursor.executemany('INSERT INTO Students (Name, Email) VALUES (?, ?)', [
        ('John Doe', 'john@example.com'),
        ('Jane Smith', 'jane@example.com'),
        ('Bob Johnson', 'bob@example.com'),
    ])
    
    cursor.executemany('INSERT INTO Cars (Make, Model, Year) VALUES (?, ?, ?)', [
        ('Toyota', 'Camry', 2020),
        ('Honda', 'Civic', 2021),
        ('Ford', 'F-150', 2019),
    ])
    
    cursor.executemany('INSERT INTO Courses (Name, Credits) VALUES (?, ?)', [
        ('Math 101', 3),
        ('Physics 201', 4),
        ('Chemistry 101', 3),
    ])
    
    # Create relationships
    cursor.executemany('INSERT INTO StudentCars (StudentId, CarId, AssignedDate) VALUES (?, ?, ?)', [
        (1, 1, '2024-01-15'),
        (2, 2, '2024-02-20'),
        (1, 3, '2024-03-10'),  # Student 1 has 2 cars
    ])
    
    cursor.executemany('INSERT INTO student_courses (student_id, course_id, enrollment_date, grade) VALUES (?, ?, ?, ?)', [
        (1, 1, '2024-01-10', 'A'),
        (1, 2, '2024-01-10', 'B+'),
        (2, 1, '2024-01-10', 'A-'),
        (2, 3, '2024-01-10', 'B'),
        (3, 2, '2024-01-10', 'A'),
    ])
    
    conn.commit()
    conn.close()
    print("✅ Test database created successfully")

async def test_relationship_queries():
    """Test various relationship queries"""
    rag = RAGService()
    
    # Create SQLite engine
    conn_string = 'sqlite:///test_relationships.db'
    connection_id = 'test_relationships'
    engine = create_engine(conn_string)
    
    # Get schema to train fuzzy matcher
    schema_analyzer = SchemaAnalyzer()
    schema = await schema_analyzer.get_database_schema(engine, connection_id, force_refresh=True)
    
    print(f"\nDatabase has {len(schema.get('tables', {}))} tables:")
    for table_name in schema.get('tables', {}).keys():
        print(f"  - {table_name}")
    
    # Teach the fuzzy matcher
    rag.schema_analyzer.fuzzy_matcher.learn_from_schema(schema)
    rag.fuzzy_corrector.learn_from_schema(schema)
    
    print("\n" + "="*60)
    print("Testing Relationship Table Detection")
    print("="*60)
    
    # Test queries
    test_cases = [
        ("count students with cars", "StudentCars"),
        ("count students with car", "StudentCars"),  # Singular form
        ("count student with courses", "student_courses"),  # Different naming pattern
        ("show students with cars", "StudentCars"),
        ("list student with course", "student_courses"),
        ("count applications with documents", "ApplicationDocuments"),
    ]
    
    for query, expected_table in test_cases:
        print(f"\n📝 Query: \"{query}\"")
        print(f"   Expected junction table: {expected_table}")
        
        # Generate SQL
        result = await rag.generate_sql(query, schema, connection_id)
        
        if isinstance(result, tuple):
            sql = result[0]
            metadata = result[1] if len(result) > 1 else {}
        else:
            sql = result.get('sql', 'ERROR')
            metadata = result.get('metadata', {})
        
        print(f"   Generated SQL: {sql}")
        
        if expected_table.lower() in sql.lower():
            print(f"   ✅ Correctly found junction table!")
        else:
            print(f"   ❌ Junction table not found in query")
        
        # Execute the query to verify it works
        if sql and sql != "ERROR":
            try:
                import sqlite3
                conn = sqlite3.connect('test_relationships.db')
                cursor = conn.cursor()
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    print(f"   📊 Result: {result[0] if 'COUNT' in sql else f'{len(result)} rows'}")
                conn.close()
            except Exception as e:
                print(f"   ⚠️ Execution error: {e}")

async def main():
    print("🚀 Testing Intelligent Relationship Table Detection\n")
    
    # Create test database
    await create_test_database()
    
    # Test relationship queries
    await test_relationship_queries()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())