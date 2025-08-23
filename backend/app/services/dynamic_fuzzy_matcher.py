"""
Dynamic fuzzy matching service that learns from actual database schema
"""
import re
from typing import List, Dict, Tuple, Optional, Set
from fuzzywuzzy import fuzz, process
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class DynamicFuzzyMatcher:
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
        
        # These will be populated dynamically from the database
        self.actual_tables = []
        self.actual_columns = {}
        self.table_patterns = {}
        self.learned_mappings = {}
        self.compound_tables = []  # Tables that are combinations of words
        self.table_row_counts = {}  # Store row counts to prefer non-empty tables
        self.table_is_empty = {}    # Track which tables are empty
        
    def learn_from_schema(self, schema_info: Dict) -> None:
        """
        Learn patterns from the actual database schema.
        This method should be called when schema is loaded or refreshed.
        """
        if not schema_info or "tables" not in schema_info:
            logger.warning("No schema info provided to learn from")
            return
        
        logger.info(f"Learning from schema with {len(schema_info.get('tables', {}))} tables")
        
        # Clear previous learnings
        self.actual_tables = list(schema_info["tables"].keys())
        self.actual_columns = {}
        self.table_patterns = {}
        self.learned_mappings = {}
        self.compound_tables = []
        self.table_row_counts = {}
        self.table_is_empty = {}
        
        # Analyze each table name
        for table_name in self.actual_tables:
            table_lower = table_name.lower()
            table_info = schema_info["tables"][table_name]
            
            # Store row count and empty status
            row_count = table_info.get("row_count", 0)
            self.table_row_counts[table_name] = row_count
            self.table_is_empty[table_name] = table_info.get("is_empty", row_count == 0)
            
            # Store columns for this table
            if "columns" in table_info:
                self.actual_columns[table_name] = [
                    col["name"] for col in table_info["columns"]
                ]
            
            # Detect compound tables (e.g., "scholarshipapplications", "studentcourses")
            if self._is_compound_word(table_lower):
                self.compound_tables.append(table_name)
                # Extract component words
                components = self._extract_word_components(table_lower)
                for component in components:
                    if component not in self.learned_mappings:
                        self.learned_mappings[component] = []
                    self.learned_mappings[component].append(table_name)
            
            # Learn singular/plural patterns
            if table_lower.endswith('s'):
                singular = table_lower[:-1]
                self.learned_mappings[singular] = self.learned_mappings.get(singular, [])
                self.learned_mappings[singular].append(table_name)
            else:
                plural = table_lower + 's'
                self.learned_mappings[plural] = self.learned_mappings.get(plural, [])
                self.learned_mappings[plural].append(table_name)
            
            # Learn word patterns (e.g., "student" from "students", "application" from "applications")
            words = self._extract_meaningful_words(table_lower)
            for word in words:
                if word not in self.table_patterns:
                    self.table_patterns[word] = []
                self.table_patterns[word].append(table_name)
        
        logger.info(f"Learned patterns from {len(self.actual_tables)} tables")
        logger.info(f"Found {len(self.compound_tables)} compound tables")
        logger.info(f"Learned {len(self.learned_mappings)} mappings")
    
    def _is_compound_word(self, word: str) -> bool:
        """
        Detect if a word is a compound (like "scholarshipapplications").
        Uses heuristics to identify compound words.
        """
        # Common word endings that might indicate compound words
        common_words = [
            'application', 'student', 'scholarship', 'enrollment', 'course',
            'grade', 'teacher', 'professor', 'department', 'registration',
            'payment', 'transaction', 'record', 'history', 'status',
            'type', 'category', 'detail', 'info', 'data', 'log'
        ]
        
        # Check if the word contains any common words
        for common_word in common_words:
            if common_word in word and len(word) > len(common_word) + 3:
                return True
        
        # Check for camelCase or PascalCase
        if any(c.isupper() for c in word[1:]):
            return True
        
        # Check if it's unusually long (might be compound)
        if len(word) > 15:
            return True
        
        return False
    
    def _extract_word_components(self, compound_word: str) -> List[str]:
        """
        Extract component words from a compound word.
        E.g., "scholarshipapplications" -> ["scholarship", "application", "applications"]
        """
        components = []
        word_lower = compound_word.lower()
        
        # Common meaningful words to look for
        common_words = [
            'applications', 'application', 'students', 'student', 
            'scholarships', 'scholarship', 'enrollments', 'enrollment',
            'courses', 'course', 'grades', 'grade', 'teachers', 'teacher',
            'professors', 'professor', 'departments', 'department',
            'registrations', 'registration', 'payments', 'payment',
            'transactions', 'transaction', 'records', 'record',
            'history', 'status', 'types', 'type', 'categories', 'category',
            'details', 'detail', 'info', 'data', 'logs', 'log'
        ]
        
        # Try to find common words in the compound
        for word in common_words:
            if word in word_lower:
                components.append(word)
                # Also add singular/plural variant
                if word.endswith('s'):
                    components.append(word[:-1])
                else:
                    components.append(word + 's')
        
        # Also split by camelCase if present
        camel_split = re.findall(r'[A-Z][a-z]+|[a-z]+', compound_word)
        components.extend([s.lower() for s in camel_split])
        
        return list(set(components))  # Remove duplicates
    
    def _extract_meaningful_words(self, text: str) -> List[str]:
        """
        Extract meaningful words from a table name.
        """
        # Remove common prefixes/suffixes
        text = re.sub(r'^(tbl_|table_|tb_|t_)', '', text)
        text = re.sub(r'(_table|_tbl|_tb)$', '', text)
        
        # Split by underscore, hyphen, or camelCase
        words = re.findall(r'[a-z]+', text.lower())
        
        # Filter out very short words (likely not meaningful)
        words = [w for w in words if len(w) > 2]
        
        return words
    
    def soundex(self, word: str) -> str:
        """
        Generate Soundex code for a word.
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
        
        # Pad with zeros to make it 4 characters
        soundex = soundex[:4].ljust(4, '0')
        
        return soundex
    
    def find_best_table_match(self, query_term: str, threshold: int = 60) -> Optional[Tuple[str, int]]:
        """
        Find the best matching table for a query term using learned patterns.
        IMPORTANT: Prefers tables with data over empty tables when matches are similar.
        """
        if not self.actual_tables:
            return None
        
        query_lower = query_term.lower()
        candidates = []  # List of (table, base_score, has_data)
        
        # 1. Check exact match
        for table in self.actual_tables:
            if table.lower() == query_lower:
                has_data = not self.table_is_empty.get(table, False)
                candidates.append((table, 100, has_data))
        
        # 2. Check learned mappings
        if query_lower in self.learned_mappings:
            for candidate in self.learned_mappings[query_lower]:
                has_data = not self.table_is_empty.get(candidate, False)
                candidates.append((candidate, 95, has_data))
        
        # 3. Check table patterns
        if query_lower in self.table_patterns:
            for candidate in self.table_patterns[query_lower]:
                if query_lower in candidate.lower():
                    has_data = not self.table_is_empty.get(candidate, False)
                    candidates.append((candidate, 90, has_data))
        
        # 4. Check compound tables for partial matches
        for compound_table in self.compound_tables:
            if query_lower in compound_table.lower():
                has_data = not self.table_is_empty.get(compound_table, False)
                candidates.append((compound_table, 85, has_data))
        
        # 5. Use fuzzy matching
        for table in self.actual_tables:
            # Try different fuzzy matching algorithms
            scores = [
                fuzz.ratio(query_lower, table.lower()),
                fuzz.partial_ratio(query_lower, table.lower()),
                fuzz.token_sort_ratio(query_lower, table.lower()),
            ]
            
            # Boost score for substring matches
            if query_lower in table.lower() or table.lower() in query_lower:
                scores.append(85)
            
            # Check soundex similarity
            if self.soundex(query_term) == self.soundex(table):
                scores.append(80)
            
            max_score = max(scores)
            if max_score >= threshold:
                has_data = not self.table_is_empty.get(table, False)
                candidates.append((table, max_score, has_data))
        
        # Now select the best candidate
        if not candidates:
            return None
        
        logger.info(f"Candidates for '{query_term}': {candidates}")
        
        # Sort candidates by:
        # 1. Prefer tables with data (has_data = True)
        # 2. Higher score
        # 3. Shorter name (likely base table)
        candidates.sort(key=lambda x: (x[2], x[1], -len(x[0])), reverse=True)
        
        logger.info(f"Sorted candidates for '{query_term}': {candidates[:3]}")
        
        best_candidate = candidates[0]
        best_table = best_candidate[0]
        base_score = best_candidate[1]
        has_data = best_candidate[2]
        
        # Log when we choose a table with data over an empty one
        if len(candidates) > 1:
            for other in candidates[1:]:
                if abs(other[1] - base_score) <= 10:  # Similar score
                    if has_data and not other[2]:
                        logger.info(f"Chose '{best_table}' (with data) over '{other[0]}' (empty) for term '{query_term}'")
                    elif not has_data and other[2]:
                        logger.warning(f"Note: '{other[0]}' has data but '{best_table}' was chosen for '{query_term}'")
        
        # Adjust score based on data availability
        final_score = base_score
        if has_data and base_score >= 80:
            # Boost score slightly for tables with data
            final_score = min(100, base_score + 5)
        elif not has_data and base_score < 100:
            # Slightly reduce score for empty tables
            final_score = max(threshold, base_score - 5)
        
        return (best_table, final_score)
    
    def find_column_match(self, column_term: str, table_name: str = None) -> Optional[Tuple[str, str, int]]:
        """
        Find the best matching column, optionally within a specific table.
        Returns (table_name, column_name, score) or None.
        """
        column_lower = column_term.lower()
        best_match = None
        best_score = 0
        best_table = None
        
        tables_to_search = [table_name] if table_name else self.actual_tables
        
        for table in tables_to_search:
            if table not in self.actual_columns:
                continue
            
            for column in self.actual_columns[table]:
                # Exact match
                if column.lower() == column_lower:
                    return (table, column, 100)
                
                # Fuzzy match
                score = fuzz.ratio(column_lower, column.lower())
                
                # Boost for partial matches
                if column_lower in column.lower() or column.lower() in column_lower:
                    score = max(score, 85)
                
                # Soundex match
                if self.soundex(column_term) == self.soundex(column):
                    score = max(score, 75)
                
                if score > best_score:
                    best_score = score
                    best_match = column
                    best_table = table
        
        if best_score >= 60:
            return (best_table, best_match, best_score)
        
        return None
    
    def find_relationship_table(self, entity1: str, entity2: str, threshold: int = 60) -> Optional[Tuple[str, int]]:
        """
        Find a junction/relationship table between two entities.
        E.g., "student" and "car" might find "studentcars" or "student_cars" or "StudentCarAssignments"
        """
        entity1_lower = entity1.lower()
        entity2_lower = entity2.lower()
        
        # Remove trailing 's' for singular form
        entity1_singular = entity1_lower[:-1] if entity1_lower.endswith('s') else entity1_lower
        entity2_singular = entity2_lower[:-1] if entity2_lower.endswith('s') else entity2_lower
        
        candidates = []
        
        for table in self.actual_tables:
            table_lower = table.lower()
            score = 0
            has_data = not self.table_is_empty.get(table, False)
            
            # Check various patterns for junction tables
            patterns_to_check = [
                # Direct combinations
                f"{entity1_singular}{entity2_singular}",  # studentcar
                f"{entity1_singular}{entity2_lower}",     # studentcars
                f"{entity1_lower}{entity2_singular}",     # studentscar
                f"{entity1_lower}{entity2_lower}",        # studentscars
                
                # With separator
                f"{entity1_singular}_{entity2_singular}",  # student_car
                f"{entity1_singular}_{entity2_lower}",     # student_cars
                f"{entity1_lower}_{entity2_singular}",     # students_car
                f"{entity1_lower}_{entity2_lower}",        # students_cars
                
                # Reverse order
                f"{entity2_singular}{entity1_singular}",  # carstudent
                f"{entity2_singular}{entity1_lower}",     # carstudents
                f"{entity2_lower}{entity1_singular}",     # carsstudent
                f"{entity2_lower}{entity1_lower}",        # carsstudents
                
                # Reverse with separator
                f"{entity2_singular}_{entity1_singular}",  # car_student
                f"{entity2_singular}_{entity1_lower}",     # car_students
                f"{entity2_lower}_{entity1_singular}",     # cars_student
                f"{entity2_lower}_{entity1_lower}",        # cars_students
                
                # Common junction table patterns
                f"{entity1_singular}{entity2_singular}assignment",    # studentcarassignment
                f"{entity1_singular}{entity2_singular}mapping",       # studentcarmapping
                f"{entity1_singular}{entity2_singular}relationship",  # studentcarrelationship
                f"{entity1_singular}_{entity2_singular}_map",         # student_car_map
                f"{entity1_singular}_{entity2_singular}_rel",         # student_car_rel
            ]
            
            # Check if table matches any pattern
            for pattern in patterns_to_check:
                if pattern in table_lower or table_lower == pattern:
                    # Higher score for exact matches
                    if table_lower == pattern:
                        score = 100
                    else:
                        score = max(score, 85)
                    break
            
            # Also check if both entities are in the table name
            if entity1_singular in table_lower and entity2_singular in table_lower:
                score = max(score, 80)
            elif entity1_singular in table_lower and entity2_lower in table_lower:
                score = max(score, 75)
            elif entity1_lower in table_lower and entity2_singular in table_lower:
                score = max(score, 75)
            
            # Use fuzzy matching as well
            combined_term = f"{entity1_singular}{entity2_singular}"
            fuzzy_score = max(
                fuzz.ratio(combined_term, table_lower),
                fuzz.partial_ratio(combined_term, table_lower),
                fuzz.token_sort_ratio(f"{entity1_singular} {entity2_singular}", table_lower.replace('_', ' '))
            )
            score = max(score, fuzzy_score)
            
            if score >= threshold:
                candidates.append((table, score, has_data))
        
        if not candidates:
            return None
        
        # Sort by: prefer tables with data, then by score, then by shorter name
        candidates.sort(key=lambda x: (x[2], x[1], -len(x[0])), reverse=True)
        
        best_candidate = candidates[0]
        return (best_candidate[0], best_candidate[1])
    
    def suggest_query_corrections(self, query: str) -> Dict[str, any]:
        """
        Analyze a query and suggest corrections based on learned schema.
        """
        suggestions = {
            "original_query": query,
            "table_suggestions": {},
            "column_suggestions": {},
            "confidence_scores": {},
            "learned_patterns_used": []
        }
        
        # Extract potential table/column references
        words = re.findall(r'\b[a-z]+\b', query.lower())
        
        # Filter out SQL keywords
        sql_keywords = {
            'select', 'from', 'where', 'join', 'on', 'group', 'by', 'order',
            'having', 'limit', 'insert', 'update', 'delete', 'count', 'sum',
            'avg', 'max', 'min', 'and', 'or', 'not', 'with', 'as', 'all'
        }
        
        potential_refs = [w for w in words if w not in sql_keywords and len(w) > 2]
        
        # Try to match each potential reference
        for ref in potential_refs:
            # Try as table
            table_match = self.find_best_table_match(ref)
            if table_match:
                table, score = table_match
                suggestions["table_suggestions"][ref] = table
                suggestions["confidence_scores"][ref] = score
                
                # Note which pattern was used
                if ref in self.learned_mappings:
                    suggestions["learned_patterns_used"].append(f"Learned mapping: {ref} -> {table}")
                elif ref in self.table_patterns:
                    suggestions["learned_patterns_used"].append(f"Table pattern: {ref} found in {table}")
            
            # Try as column
            column_match = self.find_column_match(ref)
            if column_match:
                table, column, score = column_match
                suggestions["column_suggestions"][ref] = {"table": table, "column": column}
                if ref not in suggestions["confidence_scores"] or score > suggestions["confidence_scores"][ref]:
                    suggestions["confidence_scores"][ref] = score
        
        # Generate corrected query
        corrected_query = query
        for original, suggested_table in suggestions["table_suggestions"].items():
            if original != suggested_table:
                pattern = r'\b' + re.escape(original) + r'\b'
                corrected_query = re.sub(pattern, suggested_table, corrected_query, flags=re.IGNORECASE)
        
        if corrected_query != query:
            suggestions["suggested_query"] = corrected_query
        
        return suggestions