#!/usr/bin/env python3
"""
Create a test SQLite database with the problematic table names
to demonstrate the fuzzy matching and schema caching functionality.
"""
import sqlite3
import os
import json

# Create test database
db_path = "/home/rick/source/dbairag/backend/test_fuzzy.db"

# Remove if exists
if os.path.exists(db_path):
    os.remove(db_path)

# Create connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables with intentional typos and compound names
# This mimics the real database structure with "scholashipapplications" typo

# Students table (plural)
cursor.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    email TEXT UNIQUE,
    gpa REAL,
    enrollment_date DATE
)
""")

# Scholarship applications table with typo (scholaship instead of scholarship)
cursor.execute("""
CREATE TABLE scholashipapplications (
    id INTEGER PRIMARY KEY,
    studentid INTEGER NOT NULL,
    scholarship_name TEXT NOT NULL,
    application_date DATE,
    status TEXT,
    amount REAL,
    FOREIGN KEY (studentid) REFERENCES students(id)
)
""")

# Courses table
cursor.execute("""
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    coursecode TEXT UNIQUE,
    coursename TEXT NOT NULL,
    credits INTEGER,
    department TEXT
)
""")

# Student enrollments (compound name)
cursor.execute("""
CREATE TABLE studentenrollments (
    id INTEGER PRIMARY KEY,
    studentid INTEGER NOT NULL,
    courseid INTEGER NOT NULL,
    semester TEXT,
    grade TEXT,
    FOREIGN KEY (studentid) REFERENCES students(id),
    FOREIGN KEY (courseid) REFERENCES courses(id)
)
""")

# Insert sample data
students = [
    (1, 'John', 'Doe', 'john.doe@example.com', 3.5, '2022-09-01'),
    (2, 'Jane', 'Smith', 'jane.smith@example.com', 3.8, '2022-09-01'),
    (3, 'Bob', 'Johnson', 'bob.johnson@example.com', 3.2, '2023-01-15'),
    (4, 'Alice', 'Williams', 'alice.williams@example.com', 3.9, '2023-01-15'),
    (5, 'Charlie', 'Brown', 'charlie.brown@example.com', 3.6, '2023-09-01')
]

cursor.executemany(
    "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)",
    students
)

applications = [
    (1, 1, 'Merit Scholarship', '2023-01-10', 'approved', 5000),
    (2, 2, 'Merit Scholarship', '2023-01-12', 'approved', 5000),
    (3, 2, 'STEM Excellence Award', '2023-02-01', 'approved', 3000),
    (4, 3, 'Need-Based Grant', '2023-01-20', 'pending', 2500),
    (5, 4, 'Academic Excellence', '2023-02-15', 'approved', 7500),
    (6, 5, 'Athletic Scholarship', '2023-09-05', 'rejected', 0)
]

cursor.executemany(
    "INSERT INTO scholashipapplications VALUES (?, ?, ?, ?, ?, ?)",
    applications
)

courses = [
    (1, 'CS101', 'Introduction to Programming', 3, 'Computer Science'),
    (2, 'MATH201', 'Calculus II', 4, 'Mathematics'),
    (3, 'ENG102', 'English Composition', 3, 'English'),
    (4, 'PHY101', 'Physics I', 4, 'Physics')
]

cursor.executemany(
    "INSERT INTO courses VALUES (?, ?, ?, ?, ?)",
    courses
)

enrollments = [
    (1, 1, 1, 'Spring 2023', 'A'),
    (2, 1, 2, 'Spring 2023', 'B+'),
    (3, 2, 1, 'Spring 2023', 'A'),
    (4, 2, 3, 'Spring 2023', 'A-'),
    (5, 3, 2, 'Fall 2023', 'B'),
    (6, 4, 1, 'Fall 2023', 'A'),
    (7, 5, 4, 'Fall 2023', 'B+')
]

cursor.executemany(
    "INSERT INTO studentenrollments VALUES (?, ?, ?, ?, ?)",
    enrollments
)

# Commit and close
conn.commit()
conn.close()

print(f"✅ Test database created: {db_path}")
print("\nTable names (with intentional issues):")
print("  - students (plural)")
print("  - scholashipapplications (typo + compound)")
print("  - courses")
print("  - studentenrollments (compound)")
print("\nSample queries to test:")
print('  - "count students with applications"')
print('  - "show all student enrollments"')
print('  - "find scholarship applications"')