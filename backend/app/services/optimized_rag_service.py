import time
import logging
import json
import os
import re
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..config import settings

logger = logging.getLogger(__name__)

class OptimizedRAGService:
    """
    Enhanced schema-aware RAG service with dynamic pattern matching
    
    Features:
    - Schema Analysis: Automatically analyzes database relationships, indexes, and column types
    - Dynamic Patterns: Generates SQL based on actual database structure and column names
    - Index Optimization: Uses database indexes for performance hints
    - Typo Tolerance: Handles common typos in natural language queries
    - Extensible: Easy to add new patterns based on schema discovery
    
    Supported Dynamic Patterns:
    1. Numeric Comparisons: "students with age > 18", "gpa higher than 3.5"
    2. Date Queries: "students created since 2024", "applications this year"
    3. Text Searches: "students named John", "students from Santiago"
    4. Relationship Queries: Automatic JOIN generation based on foreign keys
    5. Aggregations: "average age", "total scholarships", "maximum score"
    6. Family Member Analysis: Complex JOIN queries with counts and thresholds
    
    Architecture:
    - _analyze_schema_relationships(): Maps database structure and relationships
    - _generate_dynamic_patterns(): Creates schema-aware SQL patterns
    - _generate_fallback_patterns(): Common patterns without schema dependency
    - _generate_index_optimized_query(): Performance optimization hints
    """
    
    def __init__(self):
        self.llm = None
        self.performance_metrics = {}
        
        if settings.openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model="gpt-4o-mini",  # Faster, cheaper model
                    temperature=0,
                    max_tokens=200,  # Limit for SQL queries
                    timeout=10.0  # 10 second timeout
                )
                logger.info("🚀 OptimizedRAGService: OpenAI configured with gpt-4o-mini")
            except Exception as e:
                logger.error(f"❌ OptimizedRAGService: OpenAI initialization failed: {e}")
                self.llm = None
        else:
            logger.info("⚠️ OptimizedRAGService: No OpenAI API key, using pattern matching only")
    
    @lru_cache(maxsize=50)
    def _get_schema_context(self, connection_id: str, schema_hash: str) -> str:
        """Cached schema context building - much faster than DB queries"""
        # This will be populated by the calling code
        return f"Schema context for connection {connection_id}"
    
    @lru_cache(maxsize=10)
    def _load_enum_mappings(self, connection_id: int = 1) -> Dict[str, Dict[str, int]]:
        """Load enum mappings from enum files dynamically"""
        enum_mappings = {}
        enum_files_dir = os.path.join(os.path.dirname(__file__), "..", "..", "enum_files")
        
        try:
            # Look for enum files for this connection
            for filename in os.listdir(enum_files_dir):
                if filename.startswith(f"{connection_id}_") and filename.endswith("_enum.json"):
                    file_path = os.path.join(enum_files_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            enum_data = json.load(f)
                            
                        # Process each enum in the file
                        for enum_name, enum_info in enum_data.get("enums", {}).items():
                            if enum_name == "ApplicationStatus":
                                # Create mapping with various text variations
                                status_mapping = {}
                                for status_key, status_data in enum_info.get("values", {}).items():
                                    status_value = status_data.get("value")
                                    status_name = status_key.lower().replace("_", " ")
                                    
                                    # Add primary name
                                    status_mapping[status_name] = status_value
                                    
                                    # Add variations
                                    if status_name == "under review":
                                        status_mapping["under_review"] = status_value
                                        status_mapping["reviewing"] = status_value
                                        status_mapping["review"] = status_value
                                    elif status_name == "approved":
                                        status_mapping["accepted"] = status_value
                                    elif status_name == "rejected":
                                        status_mapping["denied"] = status_value
                                    elif status_name == "cancelled":
                                        status_mapping["canceled"] = status_value  # US spelling
                                
                                enum_mappings["application_status"] = status_mapping
                                logger.info(f"📁 Loaded ApplicationStatus enum: {len(status_mapping)} status mappings")
                                
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        logger.warning(f"⚠️ Could not load enum file {filename}: {e}")
                        continue
                        
        except FileNotFoundError:
            logger.warning(f"⚠️ Enum files directory not found: {enum_files_dir}")
        
        # Fallback to hardcoded mappings if no files found
        if not enum_mappings:
            logger.info("📋 Using fallback hardcoded enum mappings")
            enum_mappings["application_status"] = {
                'draft': 1,
                'submitted': 2,
                'under_review': 3, 'under review': 3, 'reviewing': 3, 'review': 3,
                'approved': 4, 'accepted': 4,
                'rejected': 5, 'denied': 5,
                'cancelled': 6, 'canceled': 6
            }
        
        return enum_mappings
    
    def _build_optimized_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Build minimal, focused schema context for LLM"""
        if not schema_info or "tables" not in schema_info:
            return "No schema information available"
        
        context = "Database Schema:\n"
        tables = schema_info["tables"]
        
        # Focus on key tables and relationships
        for table_name, table_data in list(tables.items())[:5]:  # Limit to 5 tables
            context += f"\n{table_name}:\n"
            
            # Key columns only
            columns = table_data.get("columns", [])[:10]  # Limit columns
            for col in columns:
                context += f"  - {col['name']} ({col['data_type']})\n"
            
            # Foreign key relationships - CRITICAL for JOINs
            fks = table_data.get("foreign_keys", [])
            if fks:
                context += "  Relationships:\n"
                for fk in fks:
                    context += f"    {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}\n"
        
        # Add common patterns
        context += "\nCommon Patterns:\n"
        context += "- 'count X with Y' = JOIN tables and COUNT DISTINCT\n"
        context += "- Always use WITH (NOLOCK) for SELECT queries\n"
        
        return context
    
    def _analyze_schema_relationships(self, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze schema to find relationships, indexes, and queryable patterns"""
        relationships = {}
        indexed_columns = {}
        numeric_columns = {}
        date_columns = {}
        text_columns = {}
        
        if not schema_info or "tables" not in schema_info:
            return {
                "relationships": relationships,
                "indexed_columns": indexed_columns,
                "numeric_columns": numeric_columns,
                "date_columns": date_columns,
                "text_columns": text_columns
            }
        
        tables = schema_info["tables"]
        
        for table_name, table_data in tables.items():
            # Analyze columns by type for smart query generation
            columns = table_data.get("columns", [])
            for col in columns:
                col_name = col.get("name", "")
                col_type = col.get("data_type", "").lower()
                
                # Categorize columns by type
                if any(t in col_type for t in ["int", "numeric", "decimal", "float", "money"]):
                    if table_name not in numeric_columns:
                        numeric_columns[table_name] = []
                    numeric_columns[table_name].append(col_name)
                
                elif any(t in col_type for t in ["date", "time"]):
                    if table_name not in date_columns:
                        date_columns[table_name] = []
                    date_columns[table_name].append(col_name)
                
                elif any(t in col_type for t in ["char", "varchar", "text", "nchar", "nvarchar"]):
                    if table_name not in text_columns:
                        text_columns[table_name] = []
                    text_columns[table_name].append(col_name)
            
            # Analyze foreign key relationships
            fks = table_data.get("foreign_keys", [])
            for fk in fks:
                rel_key = f"{table_name}.{fk.get('column', '')}"
                rel_target = f"{fk.get('referenced_table', '')}.{fk.get('referenced_column', '')}"
                relationships[rel_key] = rel_target
            
            # Analyze indexes for performance hints
            indexes = table_data.get("indexes", [])
            for idx in indexes:
                idx_columns = idx.get("columns", [])
                if idx_columns:
                    if table_name not in indexed_columns:
                        indexed_columns[table_name] = []
                    indexed_columns[table_name].extend(idx_columns)
        
        return {
            "relationships": relationships,
            "indexed_columns": indexed_columns,
            "numeric_columns": numeric_columns,
            "date_columns": date_columns,
            "text_columns": text_columns
        }

    def _find_relationship_path(self, from_table: str, to_table: str, relationships: Dict[str, str]) -> Optional[str]:
        """Find the relationship path between two tables"""
        # Direct relationship
        for rel_key, rel_target in relationships.items():
            table_col = rel_key.split('.')
            target_table_col = rel_target.split('.')
            
            if (table_col[0] == from_table and target_table_col[0] == to_table) or \
               (table_col[0] == to_table and target_table_col[0] == from_table):
                return f"{rel_key} -> {rel_target}"
        
        return None
    
    def _generate_smart_join(self, base_table: str, target_table: str, schema_analysis: Dict[str, Any]) -> str:
        """Generate smart JOIN clause based on schema relationships"""
        relationships = schema_analysis.get("relationships", {})
        
        # Look for foreign key relationship
        for rel_key, rel_target in relationships.items():
            table_col = rel_key.split('.')
            target_table_col = rel_target.split('.')
            
            if table_col[0] == base_table and target_table_col[0] == target_table:
                return f"INNER JOIN {target_table} t2 WITH (NOLOCK) ON t1.{table_col[1]} = t2.{target_table_col[1]}"
            elif table_col[0] == target_table and target_table_col[0] == base_table:
                return f"INNER JOIN {target_table} t2 WITH (NOLOCK) ON t2.{table_col[1]} = t1.{target_table_col[1]}"
        
        # Fallback: try common patterns like Id, StudentId, etc.
        return f"INNER JOIN {target_table} t2 WITH (NOLOCK) ON t1.Id = t2.{base_table}Id"
    
    def _generate_dynamic_patterns(self, prompt_lower: str, schema_analysis: Dict[str, Any], original_prompt: str = None) -> Optional[str]:
        """Generate dynamic SQL patterns based on schema analysis"""
        relationships = schema_analysis.get("relationships", {})
        numeric_columns = schema_analysis.get("numeric_columns", {})
        date_columns = schema_analysis.get("date_columns", {})
        text_columns = schema_analysis.get("text_columns", {})
        
        # Pattern: Dynamic numeric comparisons (e.g., "students with GPA > 3.5", "age > 25")
        if "student" in prompt_lower and any(op in prompt_lower for op in ["greater", "less", "more", "fewer", ">", "<", "="]):
            numbers = re.findall(r'\d+\.?\d*', prompt_lower)
            if numbers and "Students" in numeric_columns:
                value = numbers[0]
                
                # Try to match column names dynamically
                for col in numeric_columns["Students"]:
                    col_lower = col.lower()
                    # Match common patterns
                    if any(pattern in prompt_lower for pattern in [col_lower, col_lower.replace("_", ""), col_lower.replace("_", " ")]):
                        if any(op in prompt_lower for op in ["greater", "more", ">"]):
                            logger.info(f"🎯 Dynamic pattern: Students with {col} > {value}")
                            return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE {col} > {value}"
                        elif any(op in prompt_lower for op in ["less", "fewer", "<"]):
                            logger.info(f"🎯 Dynamic pattern: Students with {col} < {value}")
                            return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE {col} < {value}"
                        elif "=" in prompt_lower or "equal" in prompt_lower:
                            logger.info(f"🎯 Dynamic pattern: Students with {col} = {value}")
                            return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE {col} = {value}"
        
        # Pattern: Dynamic date range queries (e.g., "students created this year", "applications since 2024")
        if any(time_word in prompt_lower for time_word in ["year", "month", "day", "since", "before", "after"]):
            current_year = "2024"  # Could be made dynamic
            
            for table_name, date_cols in date_columns.items():
                if table_name.lower() in prompt_lower:
                    for col in date_cols:
                        if any(time_ref in prompt_lower for time_ref in ["this year", "current year", str(current_year)]):
                            logger.info(f"🎯 Dynamic date pattern: {table_name} from this year")
                            return f"SELECT COUNT(*) AS total FROM {table_name} WITH (NOLOCK) WHERE YEAR({col}) = {current_year}"
        
        # Pattern: Dynamic text search queries with normalized city support
        if "student" in prompt_lower and any(text_op in prompt_lower for text_op in ["named", "called", "from", "in", "containing", "like"]):
            # Extract quoted strings or capitalized words (potential search terms)
            prompt = original_prompt or prompt_lower  # Use original if available
            quoted_terms = re.findall(r'"([^"]*)"', prompt_lower)
            capitalized_terms = re.findall(r'\b[A-Z][a-zA-Z\s]+\b', prompt)
            search_terms = quoted_terms + [term.strip() for term in capitalized_terms if len(term.strip()) > 2]
            
            if search_terms:
                search_term = search_terms[0]
                
                # Special handling for city-based queries using normalized structure
                if any(keyword in prompt_lower for keyword in ["from", "in"]) and any(loc in prompt_lower for loc in ["city", "location"]):
                    # Check if we have Cities table relationship
                    city_relationships = []
                    for rel_key, rel_target in relationships.items():
                        if "Students" in rel_key and "Cities" in rel_target:
                            city_relationships.append(rel_key.split('.')[1])  # Get the column name
                    
                    if city_relationships:
                        logger.info(f"🎯 Dynamic city search: Students from {search_term} (schema-aware)")
                        # Use the detected city relationship columns
                        join_conditions = []
                        where_conditions = []
                        for i, city_col in enumerate(city_relationships):
                            join_alias = f"c{i+1}"
                            join_conditions.append(f"LEFT JOIN Cities {join_alias} WITH (NOLOCK) ON s.{city_col} = {join_alias}.Id")
                            where_conditions.append(f"{join_alias}.Name LIKE '%{search_term}%'")
                        
                        return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                                  FROM Students s WITH (NOLOCK) 
                                  {' '.join(join_conditions)}
                                  WHERE {' OR '.join(where_conditions)}"""
                
                # Regular text search for other columns
                if "Students" in text_columns:
                    for col in text_columns["Students"]:
                        col_lower = col.lower()
                        if any(pattern in prompt_lower for pattern in [
                            f"{col_lower}", f"{col_lower.replace('_', '')}", f"{col_lower.replace('_', ' ')}"
                        ]) or any(keyword in prompt_lower for keyword in ["named", "called"] if "name" in col_lower):
                            
                            logger.info(f"🎯 Dynamic text search: Students where {col} contains '{search_term}'")
                            return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE {col} LIKE '%{search_term}%'"
        
        # Pattern: Dynamic aggregation queries (e.g., "average age of students", "total scholarships")
        if any(agg in prompt_lower for agg in ["average", "avg", "sum", "total", "maximum", "max", "minimum", "min"]):
            if "Students" in numeric_columns:
                for col in numeric_columns["Students"]:
                    col_lower = col.lower()
                    if any(pattern in prompt_lower for pattern in [col_lower, col_lower.replace("_", ""), col_lower.replace("_", " ")]):
                        if any(agg in prompt_lower for agg in ["average", "avg"]):
                            logger.info(f"🎯 Dynamic aggregation: Average {col}")
                            return f"SELECT AVG(CAST({col} AS FLOAT)) AS average FROM Students WITH (NOLOCK)"
                        elif any(agg in prompt_lower for agg in ["sum", "total"]):
                            logger.info(f"🎯 Dynamic aggregation: Sum of {col}")
                            return f"SELECT SUM({col}) AS total FROM Students WITH (NOLOCK)"
                        elif any(agg in prompt_lower for agg in ["maximum", "max"]):
                            logger.info(f"🎯 Dynamic aggregation: Maximum {col}")
                            return f"SELECT MAX({col}) AS maximum FROM Students WITH (NOLOCK)"
                        elif any(agg in prompt_lower for agg in ["minimum", "min"]):
                            logger.info(f"🎯 Dynamic aggregation: Minimum {col}")
                            return f"SELECT MIN({col}) AS minimum FROM Students WITH (NOLOCK)"
        
        # Pattern: Dynamic relationship-based queries with better table detection
        if "count" in prompt_lower:
            # Find potential table relationships in the prompt
            mentioned_tables = []
            
            # Check all table names from schema
            all_tables = set()
            for rel_key in relationships.keys():
                all_tables.add(rel_key.split('.')[0])
            for table_name in relationships.values():
                all_tables.add(table_name.split('.')[0])
            
            for table_name in all_tables:
                table_lower = table_name.lower()
                # Check for table name mentions (both exact and partial)
                if table_lower in prompt_lower or any(
                    table_part in prompt_lower for table_part in [
                        table_lower.replace('s', ''), # singular form
                        table_lower.rstrip('s'),      # remove trailing s
                        table_lower[:-1] if table_lower.endswith('s') else table_lower
                    ]
                ):
                    mentioned_tables.append(table_name)
            
            # Remove duplicates while preserving order
            mentioned_tables = list(dict.fromkeys(mentioned_tables))
            
            # If multiple tables mentioned, suggest JOIN
            if len(mentioned_tables) >= 2:
                base_table = mentioned_tables[0]
                target_table = mentioned_tables[1]
                
                # Find relationship
                relationship_path = self._find_relationship_path(base_table, target_table, relationships)
                if relationship_path:
                    join_clause = self._generate_smart_join(base_table, target_table, schema_analysis)
                    logger.info(f"🎯 Dynamic relationship pattern: {base_table} -> {target_table}")
                    return f"""SELECT COUNT(DISTINCT t1.Id) AS total 
                              FROM {base_table} t1 WITH (NOLOCK) 
                              {join_clause}"""
        
        return None
    
    def _generate_index_optimized_query(self, base_query: str, table_name: str, schema_analysis: Dict[str, Any]) -> str:
        """Optimize query based on available indexes"""
        indexed_columns = schema_analysis.get("indexed_columns", {})
        
        if table_name in indexed_columns:
            # Add hints for indexed columns if they appear in WHERE clauses
            for col in indexed_columns[table_name]:
                if col in base_query and "WHERE" in base_query:
                    # Query already uses indexed column, it's good
                    logger.info(f"🔍 Query uses indexed column {col} for optimal performance")
                    break
        
        return base_query
    
    def _generate_fallback_patterns(self, prompt_lower: str, original_prompt: str = None) -> Optional[str]:
        """Generate common patterns without requiring full schema analysis"""
        
        # Pattern: Age-based queries (common column names)
        if "student" in prompt_lower and "age" in prompt_lower and any(op in prompt_lower for op in ["greater", "more", "older", ">", "above"]):
            numbers = re.findall(r'\d+', prompt_lower)
            if numbers:
                age = numbers[0]
                logger.info(f"🎯 Fallback pattern: Students older than {age}")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE Age > {age}"
        
        if "student" in prompt_lower and "age" in prompt_lower and any(op in prompt_lower for op in ["less", "fewer", "younger", "<", "under"]):
            numbers = re.findall(r'\d+', prompt_lower)
            if numbers:
                age = numbers[0]
                logger.info(f"🎯 Fallback pattern: Students younger than {age}")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE Age < {age}"
        
        # Pattern: GPA-based queries
        if "student" in prompt_lower and "gpa" in prompt_lower and any(op in prompt_lower for op in ["greater", "more", "above", ">", "higher"]):
            numbers = re.findall(r'\d+\.?\d*', prompt_lower)
            if numbers:
                gpa = numbers[0]
                logger.info(f"🎯 Fallback pattern: Students with GPA > {gpa}")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE GPA > {gpa}"
        
        # Pattern: City/Location-based queries with normalized structure support
        if "student" in prompt_lower and any(loc in prompt_lower for loc in ["from", "in", "city", "location"]):
            # Extract quoted strings or capitalized words (city names)
            prompt = original_prompt or prompt_lower  # Use original if available
            quoted_terms = re.findall(r'"([^"]*)"', prompt)  # Use original prompt to preserve case
            capitalized_terms = re.findall(r'\b[A-Z][a-zA-Z\s]+\b', prompt)  # Use original prompt to preserve case
            search_terms = quoted_terms + [term.strip() for term in capitalized_terms if len(term.strip()) > 2 and term.strip().lower() not in ["Count", "Students", "From"]]
            
            if search_terms:
                location = search_terms[0]
                logger.info(f"🎯 Fallback pattern: Students from {location} (normalized)")
                
                # Handle normalized Cities table structure
                # Students can be linked via CityIdPhysical or CityIdPostal
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK) 
                          LEFT JOIN Cities c1 WITH (NOLOCK) ON s.CityIdPhysical = c1.Id 
                          LEFT JOIN Cities c2 WITH (NOLOCK) ON s.CityIdPostal = c2.Id 
                          WHERE c1.Name LIKE '%{location}%' 
                             OR c2.Name LIKE '%{location}%'"""
        
        # Pattern: Name-based queries
        if "student" in prompt_lower and any(name_op in prompt_lower for name_op in ["named", "called", "name"]):
            quoted_terms = re.findall(r'"([^"]*)"', prompt_lower)
            capitalized_terms = re.findall(r'\b[A-Z][a-z]+\b', prompt_lower)
            search_terms = quoted_terms + capitalized_terms
            
            if search_terms:
                name = search_terms[0]
                logger.info(f"🎯 Fallback pattern: Students named {name}")
                # Try multiple common name column patterns
                return f"""SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) 
                          WHERE FirstName LIKE '%{name}%' 
                             OR LastName LIKE '%{name}%' 
                             OR FullName LIKE '%{name}%'"""
        
        # Pattern: Year-based queries (for any year column)
        if any(time_word in prompt_lower for time_word in ["year", "since", "after", "before"]) and any(num in prompt_lower for num in ["2020", "2021", "2022", "2023", "2024", "2025"]):
            years = re.findall(r'20\d{2}', prompt_lower)
            if years and "student" in prompt_lower:
                year = years[0]
                if "since" in prompt_lower or "after" in prompt_lower:
                    logger.info(f"🎯 Fallback pattern: Students since {year}")
                    return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE YEAR(CreatedAt) >= {year}"
                elif "before" in prompt_lower:
                    logger.info(f"🎯 Fallback pattern: Students before {year}")
                    return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE YEAR(CreatedAt) < {year}"
                else:
                    logger.info(f"🎯 Fallback pattern: Students from {year}")
                    return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE YEAR(CreatedAt) = {year}"
        
        # Pattern: Status-based queries with smart matching
        if "student" in prompt_lower and "status" in prompt_lower:
            # Look for status keywords
            status_keywords = ["active", "inactive", "pending", "approved", "rejected", "enrolled", "graduated"]
            for keyword in status_keywords:
                if keyword in prompt_lower:
                    logger.info(f"🎯 Fallback pattern: Students with status {keyword}")
                    return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE Status LIKE '%{keyword}%' OR StatusText LIKE '%{keyword}%'"
        
        # Pattern: User role-based queries (show users, board members, etc.)
        if ("user" in prompt_lower or "member" in prompt_lower) and any(action in prompt_lower for action in ["show", "list", "count", "find"]):
            # Define role mappings for different ways to express roles
            role_mappings = {
                'board member': 'BoardMember',
                'boardmember': 'BoardMember', 
                'admin': 'Administrator',
                'administrator': 'Administrator',
                'student': 'Student',
                'staff': 'Staff',
                'faculty': 'Faculty',
                'teacher': 'Teacher',
                'instructor': 'Instructor',
                'coordinator': 'Coordinator',
                'manager': 'Manager',
                'director': 'Director',
                'supervisor': 'Supervisor'
            }
            
            # Check for specific role patterns
            for role_key, role_value in role_mappings.items():
                if role_key in prompt_lower:
                    # Determine if it's a count or show query
                    if "count" in prompt_lower:
                        logger.info(f"🎯 Fallback pattern: Count ASP.NET users with role {role_value}")
                        return f"""SELECT COUNT(DISTINCT u.Id) AS total 
                                  FROM AspNetUsers u WITH (NOLOCK)
                                  INNER JOIN AspNetUserRoles ur WITH (NOLOCK) ON u.Id = ur.UserId
                                  INNER JOIN AspNetRoles r WITH (NOLOCK) ON ur.RoleId = r.Id
                                  WHERE r.Name LIKE '%{role_value}%'"""
                    else:
                        # Extract limit if specified, default to 100
                        numbers = re.findall(r'\d+', prompt_lower)
                        limit = int(numbers[0]) if numbers else 100
                        
                        logger.info(f"🎯 Fallback pattern: Show {limit} ASP.NET users with role {role_value}")
                        return f"""SELECT TOP {limit} u.Id, u.UserName, u.Email, r.Name as Role
                                  FROM AspNetUsers u WITH (NOLOCK)
                                  INNER JOIN AspNetUserRoles ur WITH (NOLOCK) ON u.Id = ur.UserId
                                  INNER JOIN AspNetRoles r WITH (NOLOCK) ON ur.RoleId = r.Id
                                  WHERE r.Name LIKE '%{role_value}%'
                                  ORDER BY u.UserName"""
        
        return None

    def _pattern_match_sql(self, prompt: str, schema_info: Dict[str, Any], connection_id: int = 1) -> Optional[str]:
        """Enhanced pattern matching with schema awareness"""
        prompt_lower = prompt.lower().strip()
        logger.info(f"🔍 Pattern matching called for: '{prompt}' (connection: {connection_id})")
        
        # Analyze schema for smart query generation
        schema_analysis = self._analyze_schema_relationships(schema_info)
        
        # Load dynamic enum mappings
        enum_mappings = self._load_enum_mappings(connection_id)
        status_mappings = enum_mappings.get("application_status", {})
        
        # Try dynamic patterns first (even with limited schema)
        dynamic_result = self._generate_dynamic_patterns(prompt_lower, schema_analysis, prompt)
        if dynamic_result:
            return self._generate_index_optimized_query(dynamic_result, "Students", schema_analysis)
        
        # High-priority: Students with/without documents queries
        if "student" in prompt_lower and any(doc_ref in prompt_lower for doc_ref in ["document", "submission"]):
            # Check for specific document types first (highest priority)
            document_types = {
                'declaracion jurada': 'Declaracion Jurada',
                'declaración jurada': 'Declaracion Jurada',
                'birth certificate': 'Birth Certificate',
                'certificado nacimiento': 'Birth Certificate',
                'academic transcript': 'Academic Transcript',
                'transcript': 'Academic Transcript',
                'expediente': 'Academic Transcript',
                'recommendation letter': 'Recommendation Letter',
                'carta recomendacion': 'Recommendation Letter',
                'personal statement': 'Personal Statement',
                'declaracion personal': 'Personal Statement',
                'passport': 'Passport',
                'pasaporte': 'Passport',
                'id card': 'ID Card',
                'cedula': 'ID Card',
                'financial aid': 'Financial Aid Document',
                'ayuda financiera': 'Financial Aid Document'
            }
            
            # Check for specific document type patterns
            for doc_type_key, doc_type_value in document_types.items():
                if doc_type_key in prompt_lower:
                    # Check for negative patterns with specific document type
                    if any(neg_pattern in prompt_lower for neg_pattern in ["no ", "without ", "missing ", "don't have", "haven't submitted"]):
                        logger.info(f"🎯 Priority pattern: Students WITHOUT {doc_type_value} documents")
                        
                        return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                                  FROM Students s WITH (NOLOCK)
                                  LEFT JOIN StudentDocuments sd WITH (NOLOCK) ON s.Id = sd.StudentId
                                  LEFT JOIN StudentDocumentTypes sdt WITH (NOLOCK) ON sd.DocumentTypeId = sdt.Id
                                  WHERE sd.StudentId IS NULL 
                                     OR sdt.Name NOT LIKE '%{doc_type_value}%'
                                  GROUP BY s.Id
                                  HAVING COUNT(CASE WHEN sdt.Name LIKE '%{doc_type_value}%' THEN 1 END) = 0"""
                    
                    # Check for positive patterns with specific document type
                    else:
                        logger.info(f"🎯 Priority pattern: Students WITH {doc_type_value} documents")
                        
                        return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                                  FROM Students s WITH (NOLOCK)
                                  INNER JOIN StudentDocuments sd WITH (NOLOCK) ON s.Id = sd.StudentId
                                  INNER JOIN StudentDocumentTypes sdt WITH (NOLOCK) ON sd.DocumentTypeId = sdt.Id
                                  WHERE sdt.Name LIKE '%{doc_type_value}%'"""
            
            # Check for negative patterns first (no documents, without documents, missing documents)
            if any(neg_pattern in prompt_lower for neg_pattern in ["no document", "without document", "missing document", "no submission"]):
                logger.info(f"🎯 Priority pattern: Students with no documents (normalized document tables)")
                
                # Use LEFT JOIN to find students with no documents in StudentDocuments table
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK)
                          LEFT JOIN StudentDocuments sd WITH (NOLOCK) ON s.Id = sd.StudentId
                          WHERE sd.StudentId IS NULL"""
            
            # Check for positive patterns (with documents, have documents)
            elif any(pos_pattern in prompt_lower for pos_pattern in ["with document", "have document", "submitted document", "with submission"]):
                logger.info(f"🎯 Priority pattern: Students with documents (normalized document tables)")
                
                # Use INNER JOIN to find students who have documents
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK)
                          INNER JOIN StudentDocuments sd WITH (NOLOCK) ON s.Id = sd.StudentId"""
            
            # Generic document counting patterns
            elif "count" in prompt_lower:
                # Extract numbers for document count filtering
                numbers = re.findall(r'\d+', prompt_lower)
                if numbers and any(comp in prompt_lower for comp in ["more than", "greater", "over", "above", ">"]):
                    doc_count = numbers[0]
                    logger.info(f"🎯 Priority pattern: Students with more than {doc_count} documents")
                    
                    return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                              FROM Students s WITH (NOLOCK)
                              INNER JOIN (
                                  SELECT StudentId, COUNT(*) as doc_count
                                  FROM StudentDocuments WITH (NOLOCK)
                                  GROUP BY StudentId
                                  HAVING COUNT(*) > {doc_count}
                              ) dc ON s.Id = dc.StudentId"""
                
                elif numbers and any(comp in prompt_lower for comp in ["less than", "fewer", "under", "below", "<"]):
                    doc_count = numbers[0]
                    logger.info(f"🎯 Priority pattern: Students with less than {doc_count} documents")
                    
                    return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                              FROM Students s WITH (NOLOCK)
                              LEFT JOIN (
                                  SELECT StudentId, COUNT(*) as doc_count
                                  FROM StudentDocuments WITH (NOLOCK)
                                  GROUP BY StudentId
                              ) dc ON s.Id = dc.StudentId
                              WHERE ISNULL(dc.doc_count, 0) < {doc_count}"""
        
        # High-priority: Normalized Cities table queries (move before other patterns)
        if "student" in prompt_lower and "from" in prompt_lower:
            # Extract city names - use a simpler approach first
            words_after_from = prompt.split('from')
            if len(words_after_from) > 1:
                # Get everything after "from" and extract the city name
                remaining_text = words_after_from[-1].strip()
                # Simple extraction - take the next 1-3 words that are capitalized
                city_words = []
                for word in remaining_text.split():
                    if word[0].isupper() and word.lower() not in ["the", "a", "an"]:
                        city_words.append(word)
                    elif city_words:  # Stop when we hit a non-capitalized word after starting
                        break
                
                if city_words:
                    location = ' '.join(city_words)
                    logger.info(f"🎯 Priority pattern: Students from {location} (normalized Cities table)")
                    
                    # Use normalized Cities table with both physical and postal addresses
                    return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                              FROM Students s WITH (NOLOCK) 
                              LEFT JOIN Cities c1 WITH (NOLOCK) ON s.CityIdPhysical = c1.Id 
                              LEFT JOIN Cities c2 WITH (NOLOCK) ON s.CityIdPostal = c2.Id 
                              WHERE c1.Name LIKE '%{location}%' 
                                 OR c2.Name LIKE '%{location}%'"""
        
        # Fallback dynamic patterns without schema dependency
        fallback_result = self._generate_fallback_patterns(prompt_lower, prompt)
        if fallback_result:
            return fallback_result
        
        # Pattern: count students with family members (check this BEFORE generic count patterns)
        # Handle typos like "familiy" and "then" instead of "than"
        if ("count" in prompt_lower and "student" in prompt_lower and 
            any(word in prompt_lower for word in ["family", "familiy", "familymember"]) and 
            any(word in prompt_lower for word in ["member", "members"])):
            # Extract the number from the prompt
            numbers = re.findall(r'\d+', prompt_lower)
            threshold = int(numbers[0]) if numbers else 1
            
            # Check for "more than" or "greater than" or ">" or "then" (common typo for "than")
            if any(phrase in prompt_lower for phrase in ["more than", "more then", "greater than", "greater then", ">", "over"]):
                logger.info(f"🎯 Pattern matched: count students with more than {threshold} family members (using JOIN)")
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK) 
                          INNER JOIN (
                              SELECT StudentId, COUNT(*) as family_count 
                              FROM FamilyMembers WITH (NOLOCK) 
                              GROUP BY StudentId 
                              HAVING COUNT(*) > {threshold}
                          ) fm ON s.Id = fm.StudentId"""
            # Check for "less than" or "<"
            elif any(phrase in prompt_lower for phrase in ["less than", "less then", "<", "under", "fewer"]):
                logger.info(f"🎯 Pattern matched: count students with less than {threshold} family members (using JOIN)")
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK) 
                          LEFT JOIN (
                              SELECT StudentId, COUNT(*) as family_count 
                              FROM FamilyMembers WITH (NOLOCK) 
                              GROUP BY StudentId
                          ) fm ON s.Id = fm.StudentId
                          WHERE ISNULL(fm.family_count, 0) < {threshold}"""
            # Check for exact match or "with X" pattern
            else:
                logger.info(f"🎯 Pattern matched: count students with exactly {threshold} family members (using JOIN)")
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK) 
                          INNER JOIN (
                              SELECT StudentId, COUNT(*) as family_count 
                              FROM FamilyMembers WITH (NOLOCK) 
                              GROUP BY StudentId 
                              HAVING COUNT(*) = {threshold}
                          ) fm ON s.Id = fm.StudentId"""
        
        # Pattern: count students by application status with totals
        if all(word in prompt_lower for word in ["count", "student"]) and ("status" in prompt_lower or "application" in prompt_lower) and any(word in prompt_lower for word in ["group", "by", "each", "breakdown", "total"]):
            logger.info("🎯 Pattern matched: count students grouped by application status with total")
            # Build CASE statement for status text - use primary names only
            primary_statuses = {
                1: "DRAFT",
                2: "SUBMITTED", 
                3: "UNDER_REVIEW",
                4: "APPROVED",
                5: "REJECTED",
                6: "CANCELLED"
            }
            case_statements = []
            for status_value, status_text in primary_statuses.items():
                case_statements.append(f"WHEN {status_value} THEN '{status_text}'")
            case_sql = " ".join(case_statements)
            
            # Use GROUPING SETS for totals
            return f"""SELECT 
    CASE 
        WHEN GROUPING(sa.Status) = 1 THEN 'TOTAL'
        ELSE CASE sa.Status {case_sql} ELSE 'UNKNOWN' END
    END AS Status,
    COUNT(DISTINCT s.Id) AS Count
FROM Students s WITH (NOLOCK)
INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId
GROUP BY GROUPING SETS ((sa.Status), ())
ORDER BY GROUPING(sa.Status), sa.Status"""
        
        # Pattern: count students with specific application status
        if all(word in prompt_lower for word in ["count", "student", "application"]) and any(status in prompt_lower for status in status_mappings.keys()):
            for status_text, status_value in status_mappings.items():
                if status_text in prompt_lower:
                    logger.info(f"🎯 Pattern matched: count students with application status {status_text}")
                    return f"SELECT COUNT(DISTINCT s.Id) AS total FROM Students s WITH (NOLOCK) INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId WHERE sa.Status = {status_value}"
        
        # Pattern: count students with applications (any status)
        if all(word in prompt_lower for word in ["count", "student", "application"]):
            logger.info("🎯 Pattern matched: count students with applications")
            return "SELECT COUNT(DISTINCT s.Id) AS total FROM Students s WITH (NOLOCK) INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId"
        
        # Pattern: show students with specific application status
        if "show" in prompt_lower and "student" in prompt_lower and "application" in prompt_lower and any(status in prompt_lower for status in status_mappings.keys()):
            # Try to extract a number from the prompt
            numbers = re.findall(r'\d+', prompt_lower)
            limit = int(numbers[0]) if numbers else 100
            
            for status_text, status_value in status_mappings.items():
                if status_text in prompt_lower:
                    logger.info(f"🎯 Pattern matched: show {limit} students with application status {status_text}")
                    return f"SELECT TOP {limit} s.*, sa.Status FROM Students s WITH (NOLOCK) INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId WHERE sa.Status = {status_value}"
        
        # Pattern: show N students (e.g., "show 5 students", "show first 10 students")
        if ("show" in prompt_lower or "first" in prompt_lower or "top" in prompt_lower) and "student" in prompt_lower and "application" not in prompt_lower:
            # Try to extract a number from the prompt
            numbers = re.findall(r'\d+', prompt_lower)
            if numbers:
                limit = int(numbers[0])
                logger.info(f"🎯 Pattern matched: show {limit} students")
                return f"SELECT TOP {limit} * FROM Students WITH (NOLOCK)"
            else:
                logger.info("🎯 Pattern matched: show students (default 100)")
                return "SELECT TOP 100 * FROM Students WITH (NOLOCK)"
        
        
        # Pattern: count total students (handle both singular and plural)
        if "count" in prompt_lower and "student" in prompt_lower and "application" not in prompt_lower:
            logger.info("🎯 Pattern matched: count total students")
            return "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK)"
        
        return None
    
    async def generate_sql_optimized(self, prompt: str, schema_info: Optional[Dict[str, Any]] = None, connection_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Optimized SQL generation with performance logging"""
        start_time = time.time()
        
        logger.info(f"🚀 OptimizedRAG: Starting SQL generation for: '{prompt}'")
        logger.info(f"🔧 OptimizedRAG: LLM available: {self.llm is not None}")
        logger.info(f"🔧 OptimizedRAG: Schema info available: {schema_info is not None}")
        logger.info(f"🔧 OptimizedRAG: Connection ID: {connection_id}")
        
        metadata = {"method": "unknown", "cached": False, "performance": {}}
        
        try:
            # Step 1: Fast pattern matching (< 1ms)
            pattern_start = time.time()
            pattern_sql = self._pattern_match_sql(prompt, schema_info or {}, connection_id or 1)
            pattern_time = time.time() - pattern_start
            
            if pattern_sql:
                metadata.update({
                    "method": "pattern_matching",
                    "pattern_match_time": f"{pattern_time*1000:.2f}ms",
                    "result_type": "table"
                })
                total_time = time.time() - start_time
                logger.info(f"✅ OptimizedRAG: Pattern match completed in {total_time*1000:.2f}ms")
                return pattern_sql, metadata
            
            # Step 2: LLM generation with optimized prompt
            if not self.llm:
                logger.warning("⚠️ OptimizedRAG: No LLM available, using basic fallback")
                fallback_sql = "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK)"
                metadata.update({
                    "method": "fallback",
                    "result_type": "table"
                })
                return fallback_sql, metadata
            
            # Build optimized context
            context_start = time.time()
            schema_context = self._build_optimized_schema_context(schema_info or {})
            context_time = time.time() - context_start
            
            # Optimized prompt template
            system_prompt = """You are an expert MSSQL query generator. Generate ONLY the SQL query, no explanations.

Rules:
- For "count X with Y": use INNER JOIN and COUNT DISTINCT
- Always add WITH (NOLOCK) for SELECT queries  
- Use proper MSSQL syntax

{schema_context}

Query request: {prompt}

SQL:"""
            
            # Fast LLM call
            llm_start = time.time()
            messages = [
                SystemMessage(content=system_prompt.format(
                    schema_context=schema_context,
                    prompt=prompt
                ))
            ]
            
            response = await self.llm.ainvoke(messages)
            sql_query = response.content.strip()
            
            # Clean up response
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            if sql_query.endswith(";"):
                sql_query = sql_query[:-1]
            
            llm_time = time.time() - llm_start
            total_time = time.time() - start_time
            
            metadata.update({
                "method": "llm_optimized",
                "context_time": f"{context_time*1000:.2f}ms",
                "llm_time": f"{llm_time*1000:.2f}ms",
                "total_time": f"{total_time*1000:.2f}ms",
                "result_type": "table",
                "schema_context_length": len(schema_context)
            })
            
            logger.info(f"✅ OptimizedRAG: LLM generation completed in {total_time*1000:.2f}ms")
            logger.info(f"🎯 OptimizedRAG: Generated SQL: {sql_query}")
            
            return sql_query, metadata
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"❌ OptimizedRAG: Error after {error_time*1000:.2f}ms: {str(e)}")
            
            # Fallback on error
            fallback_sql = "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK)"
            metadata.update({
                "method": "error_fallback",
                "error": str(e),
                "error_time": f"{error_time*1000:.2f}ms",
                "result_type": "table"
            })
            return fallback_sql, metadata
    
    def log_performance_metrics(self, operation: str, duration_ms: float, metadata: Dict[str, Any]):
        """Log detailed performance metrics"""
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []
        
        self.performance_metrics[operation].append({
            "timestamp": time.time(),
            "duration_ms": duration_ms,
            "metadata": metadata
        })
        
        # Keep only last 100 records per operation
        if len(self.performance_metrics[operation]) > 100:
            self.performance_metrics[operation] = self.performance_metrics[operation][-100:]
        
        logger.info(f"📊 Performance: {operation} completed in {duration_ms:.2f}ms")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        summary = {}
        for operation, metrics in self.performance_metrics.items():
            if metrics:
                durations = [m["duration_ms"] for m in metrics]
                summary[operation] = {
                    "count": len(metrics),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "recent_methods": [m["metadata"].get("method") for m in metrics[-10:]]
                }
        return summary

# Global instance
optimized_rag_service = OptimizedRAGService()