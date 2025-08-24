#!/usr/bin/env python3
"""
Demonstration of how the system handles column names that users might express with spaces.
Shows mapping from natural language to actual database column names.
"""

from datetime import datetime

def show_column_patterns():
    """Display how natural language maps to database columns"""
    
    print("=" * 100)
    print("🎯 COLUMN NAME PATTERN MATCHING")
    print("=" * 100)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Shows how natural language with spaces maps to database column names")
    print("=" * 100)
    
    column_mappings = [
        {
            "category": "📋 IDENTIFICATION FIELDS",
            "mappings": [
                {
                    "natural": ["identification number", "ID number", "identification", "ident"],
                    "column": "IdentificationNumber",
                    "example_query": "count students with identification number",
                    "sql": "WHERE IdentificationNumber IS NOT NULL AND IdentificationNumber != ''"
                },
                {
                    "natural": ["SSN", "social security", "social security number"],
                    "column": "SSN",
                    "example_query": "students with social security number",
                    "sql": "WHERE SSN IS NOT NULL AND SSN != ''"
                },
                {
                    "natural": ["driver's license", "drivers license", "license"],
                    "column": "DriversLicense",
                    "example_query": "students with driver's license",
                    "sql": "WHERE DriversLicense IS NOT NULL AND DriversLicense != ''"
                }
            ]
        },
        {
            "category": "📱 CONTACT INFORMATION",
            "mappings": [
                {
                    "natural": ["mobile phone", "mobile", "cell phone", "cell"],
                    "column": "MobilePhone",
                    "example_query": "count students with mobile phone",
                    "sql": "WHERE MobilePhone IS NOT NULL AND MobilePhone != ''"
                },
                {
                    "natural": ["home phone", "landline", "house phone"],
                    "column": "HomePhone",
                    "example_query": "students with home phone",
                    "sql": "WHERE HomePhone IS NOT NULL AND HomePhone != ''"
                },
                {
                    "natural": ["email", "email address", "student email"],
                    "column": "Email",
                    "example_query": "students with email",
                    "sql": "WHERE Email IS NOT NULL AND Email != ''"
                },
                {
                    "natural": ["student email", "school email"],
                    "column": "StudentEmail",
                    "example_query": "students with student email",
                    "sql": "WHERE StudentEmail IS NOT NULL AND StudentEmail != ''"
                }
            ]
        },
        {
            "category": "👤 NAME FIELDS",
            "mappings": [
                {
                    "natural": ["first name", "firstname", "given name"],
                    "column": "FirstName",
                    "example_query": "students with first name Maria",
                    "sql": "WHERE FirstName LIKE '%Maria%'"
                },
                {
                    "natural": ["last name", "lastname", "surname", "family name"],
                    "column": "LastName",
                    "example_query": "students with last name Rodriguez",
                    "sql": "WHERE LastName LIKE '%Rodriguez%'"
                },
                {
                    "natural": ["middle name", "middlename", "second name"],
                    "column": "MiddleName",
                    "example_query": "students with middle name",
                    "sql": "WHERE MiddleName IS NOT NULL AND MiddleName != ''"
                },
                {
                    "natural": ["second last name", "second surname", "mother's maiden name"],
                    "column": "SecondLastName",
                    "example_query": "students with second last name",
                    "sql": "WHERE SecondLastName IS NOT NULL AND SecondLastName != ''"
                }
            ]
        },
        {
            "category": "📍 ADDRESS FIELDS",
            "mappings": [
                {
                    "natural": ["address", "address line 1", "street address"],
                    "column": "AddressLine1",
                    "example_query": "students with address",
                    "sql": "WHERE AddressLine1 IS NOT NULL AND AddressLine1 != ''"
                },
                {
                    "natural": ["address line 2", "apartment", "unit"],
                    "column": "AddressLine2",
                    "example_query": "students with apartment number",
                    "sql": "WHERE AddressLine2 IS NOT NULL AND AddressLine2 != ''"
                },
                {
                    "natural": ["postal address", "mailing address"],
                    "column": "PostalAddressLine1",
                    "example_query": "students with postal address",
                    "sql": "WHERE PostalAddressLine1 IS NOT NULL AND PostalAddressLine1 != ''"
                },
                {
                    "natural": ["zip code", "zipcode", "postal code"],
                    "column": "ZipCode",
                    "example_query": "students with zip code 00901",
                    "sql": "WHERE ZipCode = '00901'"
                },
                {
                    "natural": ["postal zip", "mailing zip code"],
                    "column": "PostalZipCode",
                    "example_query": "students with postal zip code",
                    "sql": "WHERE PostalZipCode IS NOT NULL AND PostalZipCode != ''"
                }
            ]
        },
        {
            "category": "🎓 EDUCATION FIELDS",
            "mappings": [
                {
                    "natural": ["high school", "high school name", "school"],
                    "column": "HighSchoolName",
                    "example_query": "students from high school Central",
                    "sql": "WHERE HighSchoolName LIKE '%Central%'"
                },
                {
                    "natural": ["GPA", "grade point average", "grades"],
                    "column": "GPA",
                    "example_query": "students with GPA above 3.5",
                    "sql": "WHERE GPA > 3.5"
                },
                {
                    "natural": ["graduation date", "graduated", "graduation year"],
                    "column": "GraduationDate",
                    "example_query": "students graduated in 2024",
                    "sql": "WHERE YEAR(GraduationDate) = 2024"
                },
                {
                    "natural": ["college board", "college board score", "SAT"],
                    "column": "CollegeBoardScore",
                    "example_query": "students with college board score above 1200",
                    "sql": "WHERE CollegeBoardScore > 1200"
                }
            ]
        },
        {
            "category": "📅 DATE FIELDS",
            "mappings": [
                {
                    "natural": ["date of birth", "birth date", "DOB", "birthday"],
                    "column": "DateOfBirth",
                    "example_query": "students born after 2000",
                    "sql": "WHERE YEAR(DateOfBirth) > 2000"
                },
                {
                    "natural": ["created date", "created at", "registration date"],
                    "column": "CreatedAt",
                    "example_query": "students created this year",
                    "sql": "WHERE YEAR(CreatedAt) = 2024"
                },
                {
                    "natural": ["updated date", "updated at", "last modified"],
                    "column": "UpdatedAt",
                    "example_query": "recently updated students",
                    "sql": "WHERE UpdatedAt > DATEADD(day, -30, GETDATE())"
                }
            ]
        }
    ]
    
    for category_data in column_mappings:
        print(f"\n{category_data['category']}")
        print("-" * 80)
        
        for mapping in category_data['mappings']:
            print(f"\n📌 Database Column: {mapping['column']}")
            print(f"   Natural Language: {', '.join(f'\"{n}\"' for n in mapping['natural'])}")
            print(f"   Example Query: \"{mapping['example_query']}\"")
            print(f"   SQL Pattern: {mapping['sql']}")
    
    print("\n" + "=" * 100)
    print("🔑 KEY INSIGHTS")
    print("=" * 100)
    
    print("\n✅ Natural Language Processing:")
    print("  • System handles both spaced and non-spaced versions")
    print("  • 'mobile phone' → MobilePhone column")
    print("  • 'identification number' → IdentificationNumber column")
    print("  • 'social security number' → SSN column")
    
    print("\n✅ Pattern Recognition Features:")
    print("  • Case-insensitive matching")
    print("  • Multiple aliases for same field")
    print("  • Handles 'with' and 'without' variations")
    print("  • Supports partial matches and synonyms")
    
    print("\n✅ NULL Handling:")
    print("  • 'with' checks: IS NOT NULL AND != ''")
    print("  • 'without' checks: IS NULL OR = ''")
    print("  • Handles both NULL and empty string cases")
    
    print("\n✅ Query Optimization:")
    print("  • All queries use WITH (NOLOCK)")
    print("  • Simple WHERE clauses for index usage")
    print("  • Appropriate data type handling (strings, numbers, dates)")
    
    print("\n" + "=" * 100)
    print("✨ DEMONSTRATION COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    show_column_patterns()