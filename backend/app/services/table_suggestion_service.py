"""
Table suggestion service for intelligent error responses
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class TableSuggestionService:
    def __init__(self):
        self.similarity_threshold = 0.6
        self.max_suggestions = 3
    
    def extract_table_names_from_error(self, error_message: str, sql_query: str) -> List[str]:
        """Extract table names mentioned in error or SQL query"""
        table_names = []
        error_msg = error_message.lower()
        
        # Common patterns for missing table errors
        patterns = [
            r"invalid object name['\s]*['\"]?(\w+)['\"]?",
            r"table['\s]*['\"]?(\w+)['\"]?['\s]*doesn't exist",
            r"table['\s]*['\"]?(\w+)['\"]?['\s]*not found",
            r"no such table[:\s]*['\"]?(\w+)['\"]?",
            r"unknown table['\s]*['\"]?(\w+)['\"]?",
        ]
        
        # Extract from error message
        for pattern in patterns:
            matches = re.findall(pattern, error_msg)
            table_names.extend(matches)
        
        # Extract from SQL query using FROM and JOIN clauses
        sql_lower = sql_query.lower()
        sql_patterns = [
            r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'join\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'update\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'insert\s+into\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'delete\s+from\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, sql_lower)
            table_names.extend(matches)
        
        # Remove duplicates and clean up
        unique_tables = list(set([t.strip().strip("'\"") for t in table_names if t.strip()]))
        logger.info(f"Extracted table names from error/query: {unique_tables}")
        return unique_tables
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two table names"""
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Exact match
        if name1_lower == name2_lower:
            return 1.0
        
        # Check if one contains the other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return 0.9
        
        # Use SequenceMatcher for fuzzy matching
        similarity = SequenceMatcher(None, name1_lower, name2_lower).ratio()
        
        # Bonus for similar word patterns (singular/plural)
        if self._are_singular_plural(name1_lower, name2_lower):
            similarity += 0.2
        
        # Bonus for similar semantic meaning (cars/vehicles, users/people)
        semantic_bonus = self._get_semantic_similarity(name1_lower, name2_lower)
        similarity += semantic_bonus
        
        return min(similarity, 1.0)
    
    def _are_singular_plural(self, name1: str, name2: str) -> bool:
        """Check if two names might be singular/plural variants"""
        # Simple plural check
        if name1 + 's' == name2 or name2 + 's' == name1:
            return True
        if name1.endswith('s') and name1[:-1] == name2:
            return True
        if name2.endswith('s') and name2[:-1] == name1:
            return True
        
        # Common irregular plurals
        irregular_plurals = {
            'person': 'people', 'child': 'children', 'man': 'men', 'woman': 'women',
            'mouse': 'mice', 'goose': 'geese', 'foot': 'feet', 'tooth': 'teeth'
        }
        
        for singular, plural in irregular_plurals.items():
            if (name1 == singular and name2 == plural) or (name1 == plural and name2 == singular):
                return True
        
        return False
    
    def _get_semantic_similarity(self, name1: str, name2: str) -> float:
        """Get semantic similarity bonus for related concepts"""
        # Define semantic groups
        semantic_groups = [
            ['car', 'cars', 'vehicle', 'vehicles', 'auto', 'autos', 'automobile', 'automobiles'],
            ['user', 'users', 'person', 'people', 'customer', 'customers', 'client', 'clients'],
            ['order', 'orders', 'purchase', 'purchases', 'transaction', 'transactions'],
            ['product', 'products', 'item', 'items', 'goods', 'merchandise'],
            ['employee', 'employees', 'staff', 'worker', 'workers', 'personnel'],
            ['student', 'students', 'pupil', 'pupils', 'learner', 'learners'],
            ['book', 'books', 'publication', 'publications', 'document', 'documents'],
            ['category', 'categories', 'type', 'types', 'class', 'classes'],
            ['address', 'addresses', 'location', 'locations', 'place', 'places'],
            ['payment', 'payments', 'billing', 'invoice', 'invoices', 'receipt', 'receipts']
        ]
        
        for group in semantic_groups:
            if name1 in group and name2 in group:
                return 0.3
        
        return 0.0
    
    def suggest_tables(self, missing_tables: List[str], available_tables: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate table suggestions for missing tables"""
        suggestions = {}
        
        for missing_table in missing_tables:
            table_suggestions = []
            
            # Calculate similarity with all available tables
            similarities = []
            for available_table in available_tables:
                similarity = self.calculate_similarity(missing_table, available_table)
                if similarity >= self.similarity_threshold:
                    similarities.append({
                        'table_name': available_table,
                        'similarity': similarity,
                        'reason': self._get_suggestion_reason(missing_table, available_table, similarity)
                    })
            
            # Sort by similarity and take top suggestions
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            table_suggestions = similarities[:self.max_suggestions]
            
            if table_suggestions:
                suggestions[missing_table] = table_suggestions
                logger.info(f"Found {len(table_suggestions)} suggestions for '{missing_table}': {[s['table_name'] for s in table_suggestions]}")
            else:
                logger.info(f"No suitable suggestions found for '{missing_table}'")
        
        return suggestions
    
    def _get_suggestion_reason(self, missing: str, suggested: str, similarity: float) -> str:
        """Generate a human-readable reason for the suggestion"""
        missing_lower = missing.lower()
        suggested_lower = suggested.lower()
        
        if similarity >= 0.95:
            return "Very similar name"
        elif missing_lower in suggested_lower or suggested_lower in missing_lower:
            return "Contains the requested name"
        elif self._are_singular_plural(missing_lower, suggested_lower):
            return "Singular/plural variant"
        elif self._get_semantic_similarity(missing_lower, suggested_lower) > 0:
            return "Related concept"
        else:
            return f"Similar name ({similarity:.0%} match)"
    
    def format_suggestions_for_response(self, suggestions: Dict[str, List[Dict[str, Any]]], 
                                      original_query: str, 
                                      field_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format suggestions for API response"""
        if not suggestions:
            return {}
        
        formatted_response = {
            "has_suggestions": True,
            "suggestions": {},
            "suggested_queries": [],
            "field_insights": {},
            "data_availability": {}
        }
        
        for missing_table, table_suggestions in suggestions.items():
            formatted_response["suggestions"][missing_table] = []
            
            for suggestion in table_suggestions:
                suggestion_info = {
                    "table_name": suggestion["table_name"],
                    "similarity": round(suggestion["similarity"], 2),
                    "reason": suggestion["reason"],
                    "suggested_query": self._generate_corrected_query(original_query, missing_table, suggestion["table_name"])
                }
                formatted_response["suggestions"][missing_table].append(suggestion_info)
        
        # Generate top suggested queries
        all_suggestions = []
        for suggestions_list in suggestions.values():
            all_suggestions.extend(suggestions_list)
        
        # Sort by similarity and take top 3
        top_suggestions = sorted(all_suggestions, key=lambda x: x['similarity'], reverse=True)[:3]
        
        for suggestion in top_suggestions:
            # Find which missing table this suggestion is for
            for missing_table, table_suggestions in suggestions.items():
                if suggestion in table_suggestions:
                    corrected_query = self._generate_corrected_query(original_query, missing_table, suggestion["table_name"])
                    formatted_response["suggested_queries"].append({
                        "description": f"Use '{suggestion['table_name']}' instead of '{missing_table}' ({suggestion['reason']})",
                        "query": corrected_query,
                        "confidence": round(suggestion["similarity"], 2)
                    })
                    break
        
        # Add field analysis insights if available
        if field_analysis and "field_analysis" in field_analysis:
            analysis = field_analysis["field_analysis"]
            
            # Add data availability insights
            if "data_availability" in analysis:
                formatted_response["data_availability"] = analysis["data_availability"]
            
            # Add field insights for suggested tables
            if "tables" in analysis:
                for missing_table, table_suggestions in suggestions.items():
                    for suggestion in table_suggestions:
                        table_name = suggestion["table_name"]
                        if table_name in analysis["tables"]:
                            table_info = analysis["tables"][table_name]
                            formatted_response["field_insights"][table_name] = {
                                "entity_type": table_info.get("entity_type"),
                                "primary_concept": table_info.get("primary_concept"),
                                "available_data_domains": table_info.get("data_domains", []),
                                "field_count": len(table_info.get("fields", {})),
                                "example_fields": list(table_info.get("fields", {}).keys())[:5]
                            }
            
            # Add query capability insights
            if "query_suggestions" in analysis:
                formatted_response["query_capabilities"] = [
                    {
                        "type": qs.get("type"),
                        "description": qs.get("query_description"),
                        "example": qs.get("example_query"),
                        "confidence": qs.get("confidence", 0.0)
                    }
                    for qs in analysis["query_suggestions"][:3]  # Top 3 suggestions
                ]
        
        return formatted_response
    
    def _generate_corrected_query(self, original_query: str, old_table: str, new_table: str) -> str:
        """Generate a corrected SQL query with table name replacement"""
        # Simple replacement for now - could be enhanced with proper SQL parsing
        corrected = re.sub(
            r'\b' + re.escape(old_table) + r'\b',
            new_table,
            original_query,
            flags=re.IGNORECASE
        )
        return corrected
    
    def generate_enhanced_error_message(self, original_error: str, suggestions: Dict[str, Any]) -> str:
        """Generate an enhanced error message with suggestions"""
        if not suggestions.get("has_suggestions"):
            return original_error
        
        enhanced_message = f"{original_error}\n\n"
        enhanced_message += "💡 **Suggestions:**\n"
        
        for missing_table, table_suggestions in suggestions["suggestions"].items():
            enhanced_message += f"\nInstead of `{missing_table}`, try:\n"
            for suggestion in table_suggestions:
                enhanced_message += f"• `{suggestion['table_name']}` - {suggestion['reason']} ({suggestion['similarity']:.0%} match)\n"
        
        if suggestions["suggested_queries"]:
            enhanced_message += f"\n🔧 **Ready-to-run suggestions:**\n"
            for i, query_suggestion in enumerate(suggestions["suggested_queries"], 1):
                enhanced_message += f"{i}. {query_suggestion['description']}\n"
        
        return enhanced_message