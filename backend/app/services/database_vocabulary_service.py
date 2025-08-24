#!/usr/bin/env python3
"""
Database Vocabulary Service
Extracts and manages database schema vocabulary for improved pattern matching.
Splits compound column names, includes enums, and location data.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import json


@dataclass
class DatabaseVocabulary:
    """Comprehensive database vocabulary extracted from schema"""
    
    # Column mappings
    column_words: Dict[str, List[str]] = field(default_factory=dict)  # Column -> words
    word_to_columns: Dict[str, Set[str]] = field(default_factory=dict)  # Word -> columns
    natural_to_column: Dict[str, str] = field(default_factory=dict)  # Natural phrase -> column
    
    # Enum mappings
    enum_text_to_value: Dict[str, Dict[str, int]] = field(default_factory=dict)  # Field -> text -> value
    enum_value_to_text: Dict[str, Dict[int, str]] = field(default_factory=dict)  # Field -> value -> text
    
    # Location data
    cities: Set[str] = field(default_factory=set)
    states: Set[str] = field(default_factory=set)
    regions: Set[str] = field(default_factory=set)
    
    # Table metadata
    tables: Set[str] = field(default_factory=set)
    primary_keys: Dict[str, str] = field(default_factory=dict)  # Table -> PK
    foreign_keys: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)  # Table -> [(FK, ref_table)]
    
    # Common synonyms
    synonyms: Dict[str, List[str]] = field(default_factory=dict)


class DatabaseVocabularyService:
    """Service for extracting and managing database vocabulary"""
    
    def __init__(self):
        self.vocabulary = DatabaseVocabulary()
        self._initialize_vocabulary()
    
    def _split_compound_words(self, text: str) -> List[str]:
        """
        Split compound words into individual words.
        Examples:
        - PhoneNumber -> Phone, Number
        - FirstName -> First, Name
        - DateOfBirth -> Date, Of, Birth
        """
        # Insert spaces before capital letters
        spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        spaced = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', spaced)
        
        # Split on various delimiters
        words = re.split(r'[_\s\-]+', spaced)
        
        # Convert to lowercase and filter empty
        return [w.lower() for w in words if w]
    
    def _initialize_vocabulary(self):
        """Initialize comprehensive database vocabulary"""
        
        # Define schema
        schema = {
            "Students": {
                "columns": [
                    "StudentID", "FirstName", "LastName", "MiddleName", "SecondLastName",
                    "DateOfBirth", "IdentificationNumber", "SSN", "DriversLicense",
                    "AddressLine1", "AddressLine2", "CityIdPhysical", "StateIdPhysical",
                    "ZipCode", "PostalAddressLine1", "PostalAddressLine2", 
                    "CityIdPostal", "StateIdPostal", "PostalZipCode",
                    "MobilePhone", "HomePhone", "Email", "StudentEmail",
                    "HighSchoolName", "GraduationDate", "GPA", "CollegeBoardScore",
                    "IsActive", "CreatedAt", "UpdatedAt", "CreatedBy", "UpdatedBy"
                ],
                "primary_key": "StudentID"
            },
            "ScholarshipApplications": {
                "columns": [
                    "ApplicationID", "StudentID", "ScholarshipID", "ApplicationDate",
                    "Status", "ReviewerNotes", "SubmissionDeadline", "DecisionDate",
                    "AwardAmount", "CreatedAt", "UpdatedAt"
                ],
                "primary_key": "ApplicationID",
                "foreign_keys": [("StudentID", "Students")]
            },
            "FamilyMembers": {
                "columns": [
                    "FamilyMemberID", "StudentID", "FirstName", "LastName",
                    "Relationship", "DateOfBirth", "Occupation", "Income",
                    "IsGuardian", "PhoneNumber", "Email", "CreatedAt", "UpdatedAt"
                ],
                "primary_key": "FamilyMemberID",
                "foreign_keys": [("StudentID", "Students")]
            },
            "Documents": {
                "columns": [
                    "DocumentID", "StudentID", "DocumentType", "DocumentName",
                    "FilePath", "UploadDate", "ExpirationDate", "IsVerified",
                    "VerifiedBy", "VerificationDate", "CreatedAt", "UpdatedAt"
                ],
                "primary_key": "DocumentID",
                "foreign_keys": [("StudentID", "Students")]
            },
            "Cities": {
                "columns": [
                    "CityID", "CityName", "StateID", "CountyName",
                    "Population", "CreatedAt", "UpdatedAt"
                ],
                "primary_key": "CityID"
            },
            "States": {
                "columns": [
                    "StateID", "StateName", "StateCode", "Region",
                    "CreatedAt", "UpdatedAt"
                ],
                "primary_key": "StateID"
            }
        }
        
        # Process schema
        for table_name, table_info in schema.items():
            self.vocabulary.tables.add(table_name)
            
            # Add primary key
            if "primary_key" in table_info:
                self.vocabulary.primary_keys[table_name] = table_info["primary_key"]
            
            # Add foreign keys
            if "foreign_keys" in table_info:
                self.vocabulary.foreign_keys[table_name] = table_info["foreign_keys"]
            
            # Process columns
            for column in table_info["columns"]:
                # Split compound words
                words = self._split_compound_words(column)
                self.vocabulary.column_words[column] = words
                
                # Map words back to columns
                for word in words:
                    if word not in self.vocabulary.word_to_columns:
                        self.vocabulary.word_to_columns[word] = set()
                    self.vocabulary.word_to_columns[word].add(column)
                
                # Create natural language mappings
                natural_phrase = " ".join(words)
                self.vocabulary.natural_to_column[natural_phrase] = column
                
                # Add specific mappings for common patterns
                if column == "IdentificationNumber":
                    self.vocabulary.natural_to_column["identification number"] = column
                    self.vocabulary.natural_to_column["id number"] = column
                    self.vocabulary.natural_to_column["identification"] = column
                    self.vocabulary.natural_to_column["ident"] = column
                elif column == "SSN":
                    self.vocabulary.natural_to_column["ssn"] = column
                    self.vocabulary.natural_to_column["social security number"] = column
                    self.vocabulary.natural_to_column["social security"] = column
                elif column == "MobilePhone":
                    self.vocabulary.natural_to_column["mobile phone"] = column
                    self.vocabulary.natural_to_column["mobile"] = column
                    self.vocabulary.natural_to_column["cell phone"] = column
                    self.vocabulary.natural_to_column["cell"] = column
                elif column == "HomePhone":
                    self.vocabulary.natural_to_column["home phone"] = column
                    self.vocabulary.natural_to_column["landline"] = column
                    self.vocabulary.natural_to_column["house phone"] = column
                elif column == "DriversLicense":
                    self.vocabulary.natural_to_column["drivers license"] = column
                    self.vocabulary.natural_to_column["driver's license"] = column
                    self.vocabulary.natural_to_column["license"] = column
                elif column == "DateOfBirth":
                    self.vocabulary.natural_to_column["date of birth"] = column
                    self.vocabulary.natural_to_column["birth date"] = column
                    self.vocabulary.natural_to_column["dob"] = column
                    self.vocabulary.natural_to_column["birthday"] = column
                elif column == "GPA":
                    self.vocabulary.natural_to_column["gpa"] = column
                    self.vocabulary.natural_to_column["grade point average"] = column
                    self.vocabulary.natural_to_column["grades"] = column
                elif column == "CollegeBoardScore":
                    self.vocabulary.natural_to_column["college board score"] = column
                    self.vocabulary.natural_to_column["college board"] = column
                    self.vocabulary.natural_to_column["sat score"] = column
                    self.vocabulary.natural_to_column["sat"] = column
        
        # Initialize enum mappings
        self._initialize_enums()
        
        # Initialize location data
        self._initialize_locations()
        
        # Initialize synonyms
        self._initialize_synonyms()
    
    def _initialize_enums(self):
        """Initialize enum value mappings"""
        
        # Application Status enum
        status_enum = {
            "pending": 1,
            "submitted": 2,
            "under review": 3,
            "under_review": 3,
            "approved": 4,
            "rejected": 5,
            "cancelled": 6,
            "withdrawn": 7
        }
        
        self.vocabulary.enum_text_to_value["Status"] = status_enum
        self.vocabulary.enum_value_to_text["Status"] = {v: k for k, v in status_enum.items()}
        
        # Document Type enum
        doc_type_enum = {
            "transcript": 1,
            "id": 2,
            "proof of income": 3,
            "proof_of_income": 3,
            "recommendation": 4,
            "essay": 5,
            "certificate": 6
        }
        
        self.vocabulary.enum_text_to_value["DocumentType"] = doc_type_enum
        self.vocabulary.enum_value_to_text["DocumentType"] = {v: k for k, v in doc_type_enum.items()}
        
        # Relationship enum
        relationship_enum = {
            "mother": 1,
            "father": 2,
            "guardian": 3,
            "sibling": 4,
            "grandparent": 5,
            "other": 6
        }
        
        self.vocabulary.enum_text_to_value["Relationship"] = relationship_enum
        self.vocabulary.enum_value_to_text["Relationship"] = {v: k for k, v in relationship_enum.items()}
    
    def _initialize_locations(self):
        """Initialize location data (cities, states, regions)"""
        
        # Puerto Rico cities (with accents and common variations)
        pr_cities = {
            "Bayamón", "Bayamon",
            "San Juan",
            "Carolina",
            "Ponce",
            "Caguas",
            "Guaynabo",
            "Arecibo",
            "Toa Baja",
            "Mayagüez", "Mayaguez",
            "Trujillo Alto",
            "San Sebastián", "San Sebastian",
            "Río Grande", "Rio Grande",
            "Aguadilla",
            "Humacao",
            "Río Piedras", "Rio Piedras",
            "Fajardo",
            "Cabo Rojo",
            "Cayey",
            "Canóvanas", "Canovanas",
            "Añasco", "Anasco",
            "Gurabo",
            "Manatí", "Manati",
            "Coamo",
            "Isabela"
        }
        
        self.vocabulary.cities = pr_cities
        
        # States (for mainland US students)
        self.vocabulary.states = {
            "Puerto Rico", "PR",
            "Florida", "FL",
            "New York", "NY",
            "Texas", "TX",
            "California", "CA",
            "Pennsylvania", "PA",
            "New Jersey", "NJ",
            "Massachusetts", "MA",
            "Connecticut", "CT",
            "Illinois", "IL"
        }
        
        # Regions
        self.vocabulary.regions = {
            "Metro", "Metropolitan",
            "North", "Northern",
            "South", "Southern",
            "East", "Eastern",
            "West", "Western",
            "Central",
            "Mountain", "Montaña",
            "Coast", "Coastal"
        }
    
    def _initialize_synonyms(self):
        """Initialize common synonyms for better matching"""
        
        self.vocabulary.synonyms = {
            "student": ["students", "pupil", "pupils", "learner", "learners"],
            "count": ["total", "number", "how many", "quantity"],
            "list": ["show", "display", "get", "retrieve", "find"],
            "with": ["having", "that have", "who have", "containing"],
            "without": ["missing", "no", "lacking", "not having", "don't have"],
            "name": ["firstname", "lastname", "full name"],
            "phone": ["telephone", "contact", "number"],
            "address": ["location", "residence", "home"],
            "email": ["e-mail", "electronic mail", "contact"],
            "active": ["current", "enabled", "valid"],
            "inactive": ["disabled", "expired", "invalid"]
        }
    
    def find_column_by_natural_language(self, phrase: str) -> Optional[str]:
        """
        Find database column from natural language phrase.
        Examples:
        - "mobile phone" -> "MobilePhone"
        - "identification number" -> "IdentificationNumber"
        - "date of birth" -> "DateOfBirth"
        """
        phrase_lower = phrase.lower().strip()
        
        # Direct match
        if phrase_lower in self.vocabulary.natural_to_column:
            return self.vocabulary.natural_to_column[phrase_lower]
        
        # Try word-by-word matching
        words = phrase_lower.split()
        matching_columns = set()
        
        for word in words:
            if word in self.vocabulary.word_to_columns:
                matching_columns.update(self.vocabulary.word_to_columns[word])
        
        # Return best match (most word matches)
        if matching_columns:
            # Score columns by how many words match
            scores = {}
            for column in matching_columns:
                column_words = set(self.vocabulary.column_words[column])
                score = len(set(words) & column_words)
                scores[column] = score
            
            # Return highest scoring column
            best_column = max(scores, key=scores.get)
            if scores[best_column] > 0:
                return best_column
        
        return None
    
    def get_enum_value(self, field: str, text: str) -> Optional[int]:
        """Get numeric enum value from text"""
        if field in self.vocabulary.enum_text_to_value:
            text_lower = text.lower().strip()
            return self.vocabulary.enum_text_to_value[field].get(text_lower)
        return None
    
    def get_enum_text(self, field: str, value: int) -> Optional[str]:
        """Get text representation from enum value"""
        if field in self.vocabulary.enum_value_to_text:
            return self.vocabulary.enum_value_to_text[field].get(value)
        return None
    
    def is_location(self, text: str) -> Tuple[bool, str]:
        """
        Check if text is a location and return type.
        Returns: (is_location, location_type)
        """
        text_lower = text.lower().strip()
        
        # Check cities (case-insensitive)
        for city in self.vocabulary.cities:
            if city.lower() == text_lower:
                return True, "city"
        
        # Check states
        for state in self.vocabulary.states:
            if state.lower() == text_lower:
                return True, "state"
        
        # Check regions
        for region in self.vocabulary.regions:
            if region.lower() == text_lower:
                return True, "region"
        
        return False, ""
    
    def expand_synonyms(self, word: str) -> List[str]:
        """Expand a word to include its synonyms"""
        word_lower = word.lower()
        
        # Check if word is a key
        if word_lower in self.vocabulary.synonyms:
            return [word_lower] + self.vocabulary.synonyms[word_lower]
        
        # Check if word is a synonym value
        for key, synonyms in self.vocabulary.synonyms.items():
            if word_lower in synonyms:
                return [key] + synonyms
        
        return [word_lower]
    
    def export_vocabulary(self) -> Dict:
        """Export vocabulary as dictionary for debugging/inspection"""
        return {
            "tables": list(self.vocabulary.tables),
            "columns": {
                table: [col for col in self.vocabulary.column_words.keys() 
                       if col in schema_cols]
                for table, schema_cols in [
                    ("Students", ["StudentID", "FirstName", "LastName"]),  # Sample
                ]
            },
            "natural_mappings": dict(self.vocabulary.natural_to_column),
            "enums": {
                field: dict(values)
                for field, values in self.vocabulary.enum_text_to_value.items()
            },
            "locations": {
                "cities": list(self.vocabulary.cities)[:10],  # Sample
                "states": list(self.vocabulary.states)[:5],
                "regions": list(self.vocabulary.regions)
            },
            "synonyms": dict(self.vocabulary.synonyms)
        }
    
    def get_vocabulary_stats(self) -> Dict:
        """Get statistics about the vocabulary"""
        return {
            "total_columns": len(self.vocabulary.column_words),
            "total_words": len(self.vocabulary.word_to_columns),
            "total_natural_mappings": len(self.vocabulary.natural_to_column),
            "total_enums": len(self.vocabulary.enum_text_to_value),
            "total_cities": len(self.vocabulary.cities),
            "total_states": len(self.vocabulary.states),
            "total_synonyms": len(self.vocabulary.synonyms),
            "tables": list(self.vocabulary.tables)
        }


# Singleton instance
_vocabulary_service = None

def get_vocabulary_service() -> DatabaseVocabularyService:
    """Get singleton instance of vocabulary service"""
    global _vocabulary_service
    if _vocabulary_service is None:
        _vocabulary_service = DatabaseVocabularyService()
    return _vocabulary_service


if __name__ == "__main__":
    # Test the service
    service = get_vocabulary_service()
    
    print("Database Vocabulary Service")
    print("=" * 80)
    
    # Show stats
    stats = service.get_vocabulary_stats()
    print("\nVocabulary Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test column finding
    print("\nTesting Natural Language to Column Mapping:")
    test_phrases = [
        "mobile phone",
        "identification number",
        "date of birth",
        "social security number",
        "driver's license",
        "home phone",
        "college board",
        "grade point average"
    ]
    
    for phrase in test_phrases:
        column = service.find_column_by_natural_language(phrase)
        print(f"  '{phrase}' -> {column}")
    
    # Test enum mapping
    print("\nTesting Enum Mappings:")
    print(f"  Status 'rejected' -> {service.get_enum_value('Status', 'rejected')}")
    print(f"  Status 'approved' -> {service.get_enum_value('Status', 'approved')}")
    print(f"  Status value 3 -> {service.get_enum_text('Status', 3)}")
    
    # Test location detection
    print("\nTesting Location Detection:")
    test_locations = ["Bayamón", "San Juan", "Puerto Rico", "Metro", "Orlando"]
    for loc in test_locations:
        is_loc, loc_type = service.is_location(loc)
        if is_loc:
            print(f"  '{loc}' is a {loc_type}")
        else:
            print(f"  '{loc}' is not a known location")
    
    # Export sample vocabulary
    print("\nSample Vocabulary Export:")
    vocab = service.export_vocabulary()
    print(f"  Natural mappings (first 5): {dict(list(vocab['natural_mappings'].items())[:5])}")