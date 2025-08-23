"""
SQL Fuzzy Corrector Service
Applies fuzzy matching to correct table names in SQL queries
"""
import re
from typing import Dict, Any, Optional, List, Tuple
from .dynamic_fuzzy_matcher import DynamicFuzzyMatcher
import logging

logger = logging.getLogger(__name__)

class SQLFuzzyCorrector:
    def __init__(self):
        self.fuzzy_matcher = DynamicFuzzyMatcher()
        
    def learn_from_schema(self, schema_info: Dict[str, Any]) -> None:
        """Learn from database schema for fuzzy matching"""
        self.fuzzy_matcher.learn_from_schema(schema_info)
        logger.info(f"Fuzzy corrector learned from schema with {len(self.fuzzy_matcher.actual_tables)} tables")
        
    def correct_sql_table_names(self, sql_query: str) -> Tuple[str, List[str]]:
        """
        Correct table names in SQL query using fuzzy matching.
        Returns corrected SQL and list of corrections made.
        """
        if not sql_query:
            return sql_query, []
        
        logger.info(f"Applying fuzzy correction to SQL: {sql_query[:100]}...")
        logger.info(f"Fuzzy matcher has {len(self.fuzzy_matcher.actual_tables)} tables: {self.fuzzy_matcher.actual_tables[:5]}")
        
        corrections_made = []
        corrected_sql = sql_query
        
        # Patterns to find table names in SQL
        patterns = [
            # FROM clause
            (r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'FROM'),
            # JOIN clauses
            (r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'JOIN'),
            (r'\bINNER\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'INNER JOIN'),
            (r'\bLEFT\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'LEFT JOIN'),
            (r'\bRIGHT\s+JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'RIGHT JOIN'),
            # UPDATE clause
            (r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'UPDATE'),
            # INSERT INTO clause
            (r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'INSERT INTO'),
            # DELETE FROM clause
            (r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'DELETE FROM'),
        ]
        
        # Process each pattern
        for pattern, clause_type in patterns:
            # Find all matches (case insensitive)
            matches = re.finditer(pattern, corrected_sql, re.IGNORECASE)
            
            for match in matches:
                original_table = match.group(1)
                
                # Try to find a better match using fuzzy matching
                better_match = self.fuzzy_matcher.find_best_table_match(original_table)
                
                if better_match:
                    suggested_table, confidence = better_match
                    
                    # Only correct if we found a different table with good confidence
                    if suggested_table.lower() != original_table.lower() and confidence >= 70:
                        # Replace in the SQL, preserving case of the clause
                        old_pattern = f"{clause_type} {original_table}"
                        new_pattern = f"{clause_type} {suggested_table}"
                        
                        # Case-insensitive replace
                        pattern_regex = re.compile(re.escape(old_pattern), re.IGNORECASE)
                        if pattern_regex.search(corrected_sql):
                            corrected_sql = pattern_regex.sub(new_pattern, corrected_sql, count=1)
                            corrections_made.append(f"{original_table} → {suggested_table} (confidence: {confidence})")
                            logger.info(f"Corrected table name: {original_table} → {suggested_table} (confidence: {confidence})")
        
        return corrected_sql, corrections_made
    
    def suggest_table_corrections(self, sql_query: str) -> Dict[str, Any]:
        """
        Analyze SQL query and suggest table name corrections.
        Returns suggestions without modifying the query.
        """
        suggestions = {
            "original_query": sql_query,
            "table_suggestions": {},
            "confidence_scores": {}
        }
        
        # Extract table names from SQL
        table_patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]
        
        found_tables = set()
        for pattern in table_patterns:
            matches = re.finditer(pattern, sql_query, re.IGNORECASE)
            for match in matches:
                found_tables.add(match.group(1))
        
        # Get suggestions for each table
        for table in found_tables:
            match_result = self.fuzzy_matcher.find_best_table_match(table)
            if match_result:
                suggested_table, confidence = match_result
                if suggested_table.lower() != table.lower():
                    suggestions["table_suggestions"][table] = suggested_table
                    suggestions["confidence_scores"][table] = confidence
        
        return suggestions