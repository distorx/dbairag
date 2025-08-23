#!/usr/bin/env python3
"""
Create a test database with empty and populated tables to demonstrate
the fuzzy matcher's preference for tables with data.
"""
import sqlite3
import os

# Create test database
db_path = "/home/rick/source/dbairag/backend/test_empty_tables.db"

# Remove if exists
if os.path.exists(db_path):
    os.remove(db_path)

# Create connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create EMPTY table: city (singular, empty)
cursor.execute("""
CREATE TABLE city (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    population INTEGER
)
""")
print("Created table 'city' - EMPTY")

# Create POPULATED table: cities (plural, with data)
cursor.execute("""
CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    population INTEGER
)
""")

# Insert data into cities
cities_data = [
    (1, 'New York', 'USA', 8336817),
    (2, 'Los Angeles', 'USA', 3979576),
    (3, 'Chicago', 'USA', 2693976),
    (4, 'Houston', 'USA', 2320268),
    (5, 'Phoenix', 'USA', 1680992)
]

cursor.executemany("INSERT INTO cities VALUES (?, ?, ?, ?)", cities_data)
print(f"Created table 'cities' - POPULATED with {len(cities_data)} rows")

# Create EMPTY table: product (singular, empty)
cursor.execute("""
CREATE TABLE product (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL,
    category TEXT
)
""")
print("Created table 'product' - EMPTY")

# Create POPULATED table: products (plural, with data)
cursor.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL,
    category TEXT
)
""")

products_data = [
    (1, 'Laptop', 999.99, 'Electronics'),
    (2, 'Mouse', 29.99, 'Electronics'),
    (3, 'Keyboard', 79.99, 'Electronics'),
    (4, 'Monitor', 299.99, 'Electronics'),
    (5, 'Desk', 499.99, 'Furniture')
]

cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products_data)
print(f"Created table 'products' - POPULATED with {len(products_data)} rows")

# Create POPULATED table: customer (singular, with data)
cursor.execute("""
CREATE TABLE customer (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_date DATE
)
""")

customer_data = [
    (1, 'John Doe', 'john@example.com', '2024-01-01'),
    (2, 'Jane Smith', 'jane@example.com', '2024-01-02'),
    (3, 'Bob Johnson', 'bob@example.com', '2024-01-03')
]

cursor.executemany("INSERT INTO customer VALUES (?, ?, ?, ?)", customer_data)
print(f"Created table 'customer' - POPULATED with {len(customer_data)} rows")

# Create EMPTY table: customers (plural, empty)
cursor.execute("""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_date DATE
)
""")
print("Created table 'customers' - EMPTY")

# Commit and close
conn.commit()
conn.close()

print(f"\n✅ Test database created: {db_path}")
print("\nTable summary:")
print("  - city (EMPTY) vs cities (POPULATED)")
print("  - product (EMPTY) vs products (POPULATED)")
print("  - customer (POPULATED) vs customers (EMPTY)")
print("\nExpected behavior:")
print("  - Query 'city' should prefer 'cities' (has data)")
print("  - Query 'product' should prefer 'products' (has data)")
print("  - Query 'customer' should prefer 'customer' (has data)")