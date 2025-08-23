"""
Fuzzy matching service for handling misspelled words and typos in database queries
"""
import re
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz, process
import logging

logger = logging.getLogger(__name__)

class FuzzyMatcher:
    def __init__(self):
        # Soundex algorithm implementation
        self.soundex_map = {
            'b': '1', 'f': '1', 'p': '1', 'v': '1',
            'c': '2', 'g': '2', 'j': '2', 'k': '2', 'q': '2', 's': '2', 'x': '2', 'z': '2',
            'd': '3', 't': '3',
            'l': '4',
            'm': '5', 'n': '5',
            'r': '6'
        }
        
        # Common misspellings in scholarship domain
        self.common_misspellings = {
            "student": ["studnet", "studet", "stuent", "studen", "stident", "studant"],
            "students": ["studnets", "studets", "stuents", "studens", "stidents", "studants"],
            "scholarship": ["scholership", "scholaship", "scolarship", "scholarshp", "sholarship"],
            "application": ["aplication", "applicaton", "appliction", "aplicacion"],
            "applications": ["aplications", "applicatons", "applictions", "aplicaciones"],
            "scholarshipapplication": ["scholashipapplication", "scholarshipaplication", "scholashipaplication"],
            "scholarshipapplications": ["scholashipapplications", "scholarshipaplications", "scholashipaplications"],
            "enrollment": ["enrolment", "enrollement", "enrolement"],
            "course": ["corse", "coarse", "cours"],
            "grade": ["gread", "grad"],
            "teacher": ["techer", "teecher", "teaher"],
            "university": ["univercity", "univesity", "universty"],
            "college": ["colege", "collage", "colledge"]
        }
        
        # Build reverse mapping for quick lookups
        self.misspelling_corrections = {}
        for correct, misspellings in self.common_misspellings.items():
            for misspelling in misspellings:
                self.misspelling_corrections[misspelling.lower()] = correct
        
        # Special database-specific mappings (for tables with typos in the actual database)
        # These map common terms to the actual table names including typos
        self.database_specific_mappings = {
            "application": "scholashipapplications",  # Map singular to the actual table
            "applications": "scholashipapplications",  # Map plural to the actual table
            "scholarship_application": "scholashipapplications",
            "scholarship_applications": "scholashipapplications",
            "scholarshipapplication": "scholashipapplications",
            "scholarshipapplications": "scholashipapplications"
        }
    
    def soundex(self, word: str) -> str:
        """
        Generate Soundex code for a word.
        Soundex groups similar sounding words together.
        """
        if not word:
            return ""
        
        word = word.upper()
        
        # Keep the first letter
        soundex = word[0]
        
        # Map remaining letters to numbers
        for char in word[1:]:
            if char.lower() in self.soundex_map:
                code = self.soundex_map[char.lower()]
                # Don't add duplicate codes
                if code != soundex[-1]:
                    soundex += code
        
        # Remove vowels (except first letter)
        # Pad with zeros to make it 4 characters
        soundex = soundex[:4].ljust(4, '0')
        
        return soundex
    
    def find_best_match(self, query_term: str, candidates: List[str], threshold: int = 70) -> Optional[Tuple[str, int]]:
        """
        Find the best matching candidate for a query term using fuzzy matching.
        
        Args:
            query_term: The term to match
            candidates: List of possible matches
            threshold: Minimum similarity score (0-100) to consider a match
        
        Returns:
            Tuple of (best_match, score) or None if no good match found
        """
        if not candidates:
            return None
        
        query_lower = query_term.lower()
        
        # Check for exact match first
        for candidate in candidates:
            if candidate.lower() == query_lower:
                return (candidate, 100)
        
        # Check common misspellings
        if query_lower in self.misspelling_corrections:
            corrected = self.misspelling_corrections[query_lower]
            for candidate in candidates:
                if corrected in candidate.lower():
                    return (candidate, 95)
        
        # Use fuzzy matching with different algorithms
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            # Try different fuzzy matching algorithms
            scores = [
                fuzz.ratio(query_lower, candidate.lower()),
                fuzz.partial_ratio(query_lower, candidate.lower()),
                fuzz.token_sort_ratio(query_lower, candidate.lower()),
                fuzz.token_set_ratio(query_lower, candidate.lower())
            ]
            
            # Weight partial ratio higher for substring matches
            if query_lower in candidate.lower() or candidate.lower() in query_lower:
                scores[1] = min(100, scores[1] + 20)
            
            # Check soundex similarity
            if self.soundex(query_term) == self.soundex(candidate):
                scores.append(85)  # Soundex match bonus
            
            max_score = max(scores)
            if max_score > best_score:
                best_score = max_score
                best_match = candidate
        
        if best_score >= threshold:
            return (best_match, best_score)
        
        return None
    
    def find_table_matches(self, query_terms: List[str], available_tables: List[str]) -> Dict[str, str]:
        """
        Find matching tables for multiple query terms.
        
        Returns:
            Dictionary mapping query terms to matched table names
        """
        matches = {}
        
        for term in query_terms:
            # Try to find best match for this term
            result = self.find_best_match(term, available_tables, threshold=60)
            if result:
                matches[term] = result[0]
                logger.info(f"Fuzzy matched '{term}' to '{result[0]}' with score {result[1]}")
        
        return matches
    
    def extract_table_references(self, query: str) -> List[str]:
        """
        Extract potential table references from a natural language query.
        """
        # Common SQL keywords to exclude
        sql_keywords = {
            'select', 'from', 'where', 'join', 'on', 'group', 'by', 'order',
            'having', 'limit', 'offset', 'insert', 'update', 'delete', 'into',
            'values', 'set', 'and', 'or', 'not', 'in', 'exists', 'between',
            'like', 'is', 'null', 'count', 'sum', 'avg', 'max', 'min',
            'all', 'any', 'some', 'union', 'intersect', 'except', 'distinct',
            'with', 'as', 'show', 'list', 'find', 'get', 'how', 'many', 'the'
        }
        
        # Split query into words and filter
        words = re.findall(r'\b[a-z]+\b', query.lower())
        
        # Filter out SQL keywords and very short words
        potential_tables = [
            word for word in words 
            if word not in sql_keywords and len(word) > 2
        ]
        
        # Also look for compound terms (e.g., "scholarship applications")
        query_lower = query.lower()
        if "scholarship" in query_lower and "application" in query_lower:
            potential_tables.append("scholarshipapplication")
        if "scholaship" in query_lower and "application" in query_lower:  # Handle typo
            potential_tables.append("scholashipapplication")
        
        return potential_tables
    
    def suggest_corrections(self, query: str, available_tables: List[str], available_columns: Dict[str, List[str]]) -> Dict[str, any]:
        """
        Suggest corrections for a query based on available schema.
        
        Args:
            query: The user's query
            available_tables: List of actual table names in the database
            available_columns: Dictionary mapping table names to their columns
        
        Returns:
            Dictionary with suggestions and corrections
        """
        suggestions = {
            "original_query": query,
            "potential_corrections": [],
            "table_suggestions": {},
            "column_suggestions": {},
            "confidence_score": 0
        }
        
        # Extract potential table references
        potential_tables = self.extract_table_references(query)
        
        # Find matches for each potential table
        table_matches = self.find_table_matches(potential_tables, available_tables)
        suggestions["table_suggestions"] = table_matches
        
        # Calculate overall confidence
        if table_matches:
            total_score = sum(
                self.find_best_match(term, [match], threshold=0)[1] 
                for term, match in table_matches.items()
            )
            suggestions["confidence_score"] = total_score / len(table_matches)
        
        # Generate corrected query suggestions
        corrected_query = query
        for original, corrected in table_matches.items():
            if original != corrected:
                # Use word boundaries to avoid partial replacements
                pattern = r'\b' + re.escape(original) + r'\b'
                corrected_query = re.sub(pattern, corrected, corrected_query, flags=re.IGNORECASE)
                suggestions["potential_corrections"].append({
                    "original": original,
                    "suggested": corrected,
                    "reason": f"'{original}' might be a misspelling of '{corrected}'"
                })
        
        if corrected_query != query:
            suggestions["suggested_query"] = corrected_query
        
        return suggestions
    
    def find_similar_columns(self, column_term: str, table_columns: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, int]]]:
        """
        Find similar column names across tables.
        
        Returns:
            Dictionary mapping table names to list of (column_name, similarity_score) tuples
        """
        similar_columns = {}
        
        for table, columns in table_columns.items():
            matches = []
            for column in columns:
                result = self.find_best_match(column_term, [column], threshold=60)
                if result:
                    matches.append(result)
            
            if matches:
                # Sort by score descending
                matches.sort(key=lambda x: x[1], reverse=True)
                similar_columns[table] = matches
        
        return similar_columns