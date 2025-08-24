import time
import logging
import json
import os
import re
import unicodedata
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..config import settings
from .query_optimizer_service import query_optimizer
from .database_vocabulary_service import get_vocabulary_service

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
        self.column_intelligence = None
        self.vocabulary_service = None
        
        # Initialize column intelligence service
        try:
            from .column_intelligence_service import column_intelligence
            self.column_intelligence = column_intelligence
            logger.info("✅ OptimizedRAGService: Column Intelligence Service initialized")
        except ImportError:
            logger.warning("⚠️ OptimizedRAGService: Column Intelligence Service not available")
        
        # Initialize vocabulary service
        try:
            self.vocabulary_service = get_vocabulary_service()
            logger.info("✅ OptimizedRAGService: Database Vocabulary Service initialized")
        except Exception as e:
            logger.warning(f"⚠️ OptimizedRAGService: Database Vocabulary Service not available: {e}")
    
    def _identify_standalone_tables(self, schema_info: Dict[str, Any]) -> set:
        """Identify tables that are standalone (no relationships, no indexes, likely irrelevant)"""
        standalone = set()
        tables = schema_info.get("tables", {})
        
        # Tables that are known to be standalone or less relevant
        known_standalone = {
            "__EFMigrationsHistory",  # EF migrations
            "AspNetRoleClaims", "AspNetUserClaims", "AspNetUserLogins", "AspNetUserTokens",  # ASP.NET Identity
            "AuditLogs",  # Audit logs
            "ListaExclusiones", "ListaIncusiones",  # Exclusion/inclusion lists
            "MissingDocumentIds",  # Missing IDs
            # Backup and copy tables
            "StudentDocuments_202050807_3pm",
            "StudentDocuments_Backup_20250811_055943",
            "StudentDocuments_Backup_Duplicates",
            "StudentDocuments_Backup_Production_20250723",
            "StudentDocuments_Copy",
            "StudentDocumentsRick",
            "StudentDocumentsRick2",
            "StudentDocumentsSave",
            "StudentRecomendeds_20250721",
            "StudentRecommendeds_20250815_143000",
            "StudentRecommendeds_Backup_20250811",
            "StudentToCreate",
            "CopiaAntonioEst",
            "EstudiantesExcelenciaAcademica",
            "StudentDocumemtsCepe",
            "distritos_pueblos"
        }
        
        for table_name, table_info in tables.items():
            # Add known standalone tables
            if table_name in known_standalone:
                standalone.add(table_name)
                continue
                
            # Check if table has no foreign keys (relationships)
            has_foreign_keys = bool(table_info.get("foreign_keys", []))
            
            # Check if table has no indexes (except primary key)
            indexes = table_info.get("indexes", {})
            has_meaningful_indexes = False
            for idx_name, idx_info in indexes.items():
                # Skip primary key indexes
                if "primary" not in idx_name.lower() and "pk" not in idx_name.lower():
                    has_meaningful_indexes = True
                    break
            
            # Check if table is referenced by other tables
            is_referenced = False
            for other_table_name, other_table_info in tables.items():
                if other_table_name != table_name:
                    for fk in other_table_info.get("foreign_keys", []):
                        if fk.get("referenced_table") == table_name:
                            is_referenced = True
                            break
                if is_referenced:
                    break
            
            # Table is standalone if it has no relationships and no meaningful indexes
            if not has_foreign_keys and not has_meaningful_indexes and not is_referenced:
                standalone.add(table_name)
        
        logger.info(f"🔍 Identified {len(standalone)} standalone/irrelevant tables")
        return standalone
    
    def _normalize_for_comparison(self, text: str) -> str:
        """Normalize text by removing accents for comparison"""
        # Convert to NFD (decomposed) form and filter out combining characters
        nfd = unicodedata.normalize('NFD', text)
        without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
        return without_accents.lower()
    
    def _create_accent_insensitive_pattern(self, city_name: str) -> str:
        """Create a SQL pattern that matches both accented and non-accented versions"""
        # Common accent replacements for Puerto Rican cities
        replacements = {
            'a': '[aáà]',
            'e': '[eéè]',
            'i': '[iíì]',
            'o': '[oóò]',
            'u': '[uúù]',
            'n': '[nñ]'
        }
        
        pattern = city_name.lower()
        for char, replacement in replacements.items():
            pattern = pattern.replace(char, replacement)
        
        return pattern
        
        if settings.openai_api_key and settings.openai_api_key.startswith("sk-"):
            try:
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model="gpt-4o-mini",  # Faster, cheaper model
                    temperature=0,
                    max_tokens=300,  # Increased for complex queries with full metadata
                    timeout=15.0  # 15 second timeout
                )
                logger.info("🚀 OptimizedRAGService: OpenAI configured with gpt-4o-mini and full schema awareness")
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
    
    def _build_optimized_schema_context(self, schema_info: Dict[str, Any], connection_id: str = None) -> str:
        """Build comprehensive schema context for accurate SQL generation with column semantics"""
        if not schema_info or "tables" not in schema_info:
            return "No schema information available"
        
        context = "Database Schema (Complete):\n"
        context += "=" * 50 + "\n"
        
        tables = schema_info["tables"]
        
        # Get semantic analysis if available
        semantic_analysis = None
        if self.column_intelligence and schema_info:
            semantic_analysis = self.column_intelligence.analyze_column_semantics(schema_info)
        
        # Include ALL tables with their complete metadata
        context += f"Total Tables: {len(tables)}\n\n"
        
        # Group tables by category for better organization
        student_tables = []
        location_tables = []
        application_tables = []
        family_tables = []
        auth_tables = []
        other_tables = []
        
        for table_name in tables.keys():
            if table_name.startswith('Student'):
                student_tables.append(table_name)
            elif table_name in ['Cities', 'Regions', 'Municipios', 'HighSchools']:
                location_tables.append(table_name)
            elif 'Application' in table_name or 'Question' in table_name or 'Answer' in table_name:
                application_tables.append(table_name)
            elif 'Family' in table_name or 'Occupation' in table_name or 'Dependent' in table_name:
                family_tables.append(table_name)
            elif table_name.startswith('AspNet'):
                auth_tables.append(table_name)
            else:
                other_tables.append(table_name)
        
        # Include table details with ALL metadata
        all_table_groups = [
            ("STUDENT TABLES", student_tables),
            ("LOCATION TABLES", location_tables),
            ("APPLICATION TABLES", application_tables),
            ("FAMILY TABLES", family_tables),
            ("AUTH TABLES", auth_tables),
            ("OTHER TABLES", other_tables)
        ]
        
        for group_name, table_list in all_table_groups:
            if table_list:
                context += f"\n{group_name}:\n" + "-" * 40 + "\n"
                
                for table_name in table_list:
                    table_data = tables[table_name]
                    context += f"\n{table_name}:\n"
                    
                    # Primary Keys - CRITICAL for queries
                    pks = table_data.get("primary_keys", [])
                    if pks:
                        context += f"  PRIMARY KEY: {', '.join(pks)}\n"
                    
                    # All columns with complete type info
                    columns = table_data.get("columns", [])
                    context += f"  Columns ({len(columns)}):\n"
                    for col in columns:
                        nullable = "" if col.get('nullable', True) else " NOT NULL"
                        pk_marker = " [PK]" if col.get('primary_key', False) else ""
                        context += f"    - {col['name']} ({col.get('data_type', 'unknown')}){nullable}{pk_marker}\n"
                    
                    # Foreign Keys - ESSENTIAL for JOINs
                    fks = table_data.get("foreign_keys", [])
                    if fks:
                        context += "  Foreign Keys:\n"
                        for fk in fks:
                            context += f"    - {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}\n"
                    
                    # Indexes - IMPORTANT for query optimization
                    indexes = table_data.get("indexes", [])
                    if indexes:
                        context += "  Indexes:\n"
                        for idx in indexes:
                            unique = " (UNIQUE)" if idx.get('unique', False) else ""
                            context += f"    - {idx.get('name', 'unnamed')}: {', '.join(idx.get('columns', []))}{unique}\n"
        
        # Add relationship summary for better JOIN understanding
        context += "\n\nKEY RELATIONSHIPS:\n" + "=" * 40 + "\n"
        relationships = schema_info.get("relationships", [])
        if relationships:
            # Group relationships by table
            rel_by_table = {}
            for rel in relationships:
                from_table = rel.get('from_table')
                if from_table not in rel_by_table:
                    rel_by_table[from_table] = []
                rel_by_table[from_table].append(rel)
            
            for table, rels in list(rel_by_table.items())[:10]:  # Show top 10 tables with relationships
                context += f"{table}:\n"
                for rel in rels[:3]:  # Show up to 3 relationships per table
                    context += f"  → {rel['to_table']} via {rel['from_column']} = {rel['to_column']}\n"
        
        # Add ENUM definitions if available
        if connection_id:
            try:
                enum_mappings = self._load_enum_mappings(int(connection_id))
                if enum_mappings:
                    context += "\n\nENUM DEFINITIONS:\n" + "=" * 40 + "\n"
                    for enum_name, enum_values in enum_mappings.items():
                        context += f"\n{enum_name.upper()}:\n"
                        # Group by numeric value for clarity
                        value_groups = {}
                        for text, value in enum_values.items():
                            if value not in value_groups:
                                value_groups[value] = []
                            value_groups[value].append(text)
                        
                        for value in sorted(value_groups.keys()):
                            texts = value_groups[value]
                            primary = texts[0]
                            aliases = texts[1:] if len(texts) > 1 else []
                            context += f"  {value} = {primary.upper()}"
                            if aliases:
                                context += f" (aliases: {', '.join(aliases)})"
                            context += "\n"
                    
                    context += "\nENUM USAGE:\n"
                    context += "- Use numeric values in SQL queries (e.g., Status = 3 for UNDER_REVIEW)\n"
                    context += "- Text values in prompts map to numeric values automatically\n"
                    context += "- Example: 'approved applications' translates to Status = 4\n"
            except Exception as e:
                logger.warning(f"Could not load enums for context: {e}")
        
        # Add semantic information if available
        if semantic_analysis:
            context += "\n\nCOLUMN SEMANTICS:\n" + "=" * 40 + "\n"
            
            # Add location column information
            if semantic_analysis.get('location_columns'):
                context += "\nLocation Columns (for city/region queries):\n"
                for table, cols in list(semantic_analysis['location_columns'].items())[:5]:
                    context += f"  {table}:\n"
                    for col in cols[:3]:
                        col_desc = f"    - {col['column']}"
                        if col.get('is_postal'):
                            col_desc += " (POSTAL ADDRESS)"
                        elif col.get('is_physical'):
                            col_desc += " (PHYSICAL ADDRESS)"
                        if col.get('is_id'):
                            col_desc += " -> references Cities.Id"
                        context += col_desc + "\n"
            
            # Add temporal column information
            if semantic_analysis.get('temporal_columns'):
                context += "\nTemporal Columns (for date/time queries):\n"
                for table, cols in list(semantic_analysis['temporal_columns'].items())[:5]:
                    context += f"  {table}:\n"
                    for col in cols[:3]:
                        context += f"    - {col['column']} ({col['type']})\n"
        
        # Add SQL patterns and rules
        context += "\n\nSQL PATTERNS & RULES:\n" + "=" * 40 + "\n"
        context += "- Always use WITH (NOLOCK) for SELECT queries\n"
        context += "- Use proper JOINs based on foreign key relationships\n"
        context += "- Consider indexes when ordering or filtering\n"
        context += "- Primary keys are optimal for DISTINCT operations\n"
        context += "- Table names are case-sensitive in some databases\n"
        context += "- For enum columns, use numeric values (e.g., Status = 3, not Status = 'UNDER_REVIEW')\n"
        context += "- For location queries: CityIdPhysical = physical address, CityIdPostal = mailing address\n"
        context += "- JOIN with Cities table using appropriate city column for location-based queries\n"
        
        return context
    
    def _analyze_schema_relationships(self, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze schema to find relationships, indexes, and queryable patterns"""
        relationships = {}
        indexed_columns = {}
        primary_keys = {}
        unique_columns = {}
        numeric_columns = {}
        date_columns = {}
        text_columns = {}
        boolean_columns = {}
        
        if not schema_info or "tables" not in schema_info:
            return {
                "relationships": relationships,
                "indexed_columns": indexed_columns,
                "primary_keys": primary_keys,
                "unique_columns": unique_columns,
                "numeric_columns": numeric_columns,
                "date_columns": date_columns,
                "text_columns": text_columns,
                "boolean_columns": boolean_columns
            }
        
        tables = schema_info["tables"]
        
        for table_name, table_data in tables.items():
            # Track primary keys - CRITICAL for accurate DISTINCT and JOIN operations
            pks = table_data.get("primary_keys", [])
            if pks:
                primary_keys[table_name] = pks
            
            # Analyze columns by type for smart query generation
            columns = table_data.get("columns", [])
            for col in columns:
                col_name = col.get("name", "")
                col_type = col.get("data_type", "").lower()
                
                # Categorize columns by type
                if any(t in col_type for t in ["int", "numeric", "decimal", "float", "money", "bigint", "smallint", "tinyint"]):
                    if table_name not in numeric_columns:
                        numeric_columns[table_name] = []
                    numeric_columns[table_name].append(col_name)
                
                elif any(t in col_type for t in ["date", "time", "datetime", "timestamp"]):
                    if table_name not in date_columns:
                        date_columns[table_name] = []
                    date_columns[table_name].append(col_name)
                
                elif any(t in col_type for t in ["char", "varchar", "text", "nchar", "nvarchar", "ntext"]):
                    if table_name not in text_columns:
                        text_columns[table_name] = []
                    text_columns[table_name].append(col_name)
                
                elif any(t in col_type for t in ["bit", "bool", "boolean"]):
                    if table_name not in boolean_columns:
                        boolean_columns[table_name] = []
                    boolean_columns[table_name].append(col_name)
            
            # Analyze foreign key relationships - ESSENTIAL for JOINs
            fks = table_data.get("foreign_keys", [])
            for fk in fks:
                rel_key = f"{table_name}.{fk.get('column', '')}"
                rel_target = f"{fk.get('referenced_table', '')}.{fk.get('referenced_column', '')}"
                relationships[rel_key] = rel_target
            
            # Analyze indexes for performance hints
            indexes = table_data.get("indexes", [])
            for idx in indexes:
                idx_columns = idx.get("columns", [])
                is_unique = idx.get("unique", False)
                
                if idx_columns:
                    if table_name not in indexed_columns:
                        indexed_columns[table_name] = []
                    indexed_columns[table_name].extend(idx_columns)
                    
                    # Track unique indexes separately for DISTINCT optimization
                    if is_unique:
                        if table_name not in unique_columns:
                            unique_columns[table_name] = []
                        unique_columns[table_name].extend(idx_columns)
        
        return {
            "relationships": relationships,
            "indexed_columns": indexed_columns,
            "primary_keys": primary_keys,
            "unique_columns": unique_columns,
            "numeric_columns": numeric_columns,
            "date_columns": date_columns,
            "text_columns": text_columns,
            "boolean_columns": boolean_columns
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
    
    def _generate_dynamic_patterns(self, prompt_lower: str, schema_analysis: Dict[str, Any], original_prompt: str = None, semantic_analysis: Dict[str, Any] = None) -> Optional[str]:
        """Generate dynamic SQL patterns based on schema analysis and column semantics"""
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
                if any(keyword in prompt_lower for keyword in ["from", "in"]) and any(loc in prompt_lower for loc in ["city", "location", "bayamon", "ponce", "san juan"]):
                    # Enhanced: Use semantic analysis if available
                    if semantic_analysis and 'location_columns' in semantic_analysis:
                        location_cols = semantic_analysis.get('location_columns', {}).get('Students', [])
                        city_cols = [col for col in location_cols if col['type'] == 'city' and col['is_id']]
                        
                        if city_cols:
                            logger.info(f"🎯 Semantic city search: Students from {search_term}")
                            # Determine which city column to use based on context
                            if 'postal' in prompt_lower:
                                preferred_cols = [col for col in city_cols if col['is_postal']]
                            elif 'physical' in prompt_lower or 'fisico' in prompt_lower:
                                preferred_cols = [col for col in city_cols if col['is_physical']]
                            else:
                                # Use both postal and physical
                                preferred_cols = city_cols
                            
                            if preferred_cols:
                                join_conditions = []
                                where_conditions = []
                                for i, col_info in enumerate(preferred_cols):
                                    join_alias = f"c{i+1}"
                                    join_conditions.append(f"LEFT JOIN Cities {join_alias} WITH (NOLOCK) ON s.{col_info['column']} = {join_alias}.Id")
                                    where_conditions.append(f"{join_alias}.Name LIKE '%{search_term}%'")
                                
                                # Update where conditions to use COLLATE for accent-insensitive matching
                                where_conditions_ai = []
                                for i, col_info in enumerate(preferred_cols):
                                    join_alias = f"c{i+1}"
                                    where_conditions_ai.append(f"{join_alias}.Name COLLATE Latin1_General_CI_AI LIKE '%{search_term}%'")
                                
                                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                                          FROM Students s WITH (NOLOCK) 
                                          {' '.join(join_conditions)}
                                          WHERE {' OR '.join(where_conditions_ai)}"""
                    
                    # Fallback to relationship-based detection
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
                        
                        # Update where conditions to use COLLATE for accent-insensitive matching
                        where_conditions_ai = []
                        for i, city_col in enumerate(city_relationships):
                            join_alias = f"c{i+1}"
                            where_conditions_ai.append(f"{join_alias}.Name COLLATE Latin1_General_CI_AI LIKE '%{search_term}%'")
                        
                        return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                                  FROM Students s WITH (NOLOCK) 
                                  {' '.join(join_conditions)}
                                  WHERE {' OR '.join(where_conditions_ai)}"""
                
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
    
    def _generate_vocabulary_based_query(self, prompt_lower: str, original_prompt: str = None) -> Optional[str]:
        """Generate SQL using database vocabulary service for improved pattern matching"""
        
        if not self.vocabulary_service:
            return None
        
        # Extract potential column references using vocabulary
        words = prompt_lower.split()
        detected_columns = []
        detected_enums = {}
        detected_locations = []
        
        # Check for multi-word column names (e.g., "mobile phone", "identification number")
        for i in range(len(words)):
            # Check 3-word phrases
            if i + 2 < len(words):
                phrase = " ".join(words[i:i+3])
                column = self.vocabulary_service.find_column_by_natural_language(phrase)
                if column:
                    detected_columns.append((phrase, column))
            
            # Check 2-word phrases  
            if i + 1 < len(words):
                phrase = " ".join(words[i:i+2])
                column = self.vocabulary_service.find_column_by_natural_language(phrase)
                if column:
                    detected_columns.append((phrase, column))
            
            # Check single words
            column = self.vocabulary_service.find_column_by_natural_language(words[i])
            if column:
                detected_columns.append((words[i], column))
            
            # Check for locations
            is_loc, loc_type = self.vocabulary_service.is_location(words[i])
            if is_loc:
                detected_locations.append((words[i], loc_type))
        
        # Check for enum values in the query
        for field in ["Status", "DocumentType", "Relationship"]:
            for word in words:
                enum_val = self.vocabulary_service.get_enum_value(field, word)
                if enum_val:
                    detected_enums[field] = (word, enum_val)
        
        # Pattern: Count students with/without specific columns
        if any(student_word in prompt_lower for student_word in ["student", "students", "stdent", "studet", "studnt"]):
            
            # Check for specific column queries
            for phrase, column in detected_columns:
                if phrase in prompt_lower:
                    # Check for specific values first (e.g., SSN = '000-00-0000', ID = 'ABC123')
                    if column == "SSN":
                        # Check for specific SSN value pattern
                        ssn_pattern = re.findall(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b', original_prompt or prompt_lower)
                        if ssn_pattern:
                            ssn_value = ssn_pattern[0]
                            logger.info(f"🎯 Vocabulary pattern: Students with specific SSN {ssn_value}")
                            return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE SSN = '{ssn_value}'"
                    elif column == "IdentificationNumber":
                        # Check for specific ID number value pattern
                        id_patterns = re.findall(r'\b[A-Z0-9]{6,15}\b', original_prompt or prompt_lower.upper())
                        if id_patterns:
                            id_value = id_patterns[0]
                            logger.info(f"🎯 Vocabulary pattern: Students with specific ID {id_value}")
                            return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE IdentificationNumber = '{id_value}'"
                    
                    # Determine if query is for presence or absence
                    if "without" in prompt_lower or "no " in prompt_lower or "missing" in prompt_lower:
                        logger.info(f"🎯 Vocabulary pattern: Students without {column}")
                        return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE {column} IS NULL OR {column} = ''"
                    elif "with" in prompt_lower or "have" in prompt_lower or "has" in prompt_lower:
                        logger.info(f"🎯 Vocabulary pattern: Students with {column}")
                        return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE {column} IS NOT NULL AND {column} != ''"
            
            # Check for location-based queries
            if detected_locations:
                location, loc_type = detected_locations[0]
                logger.info(f"🎯 Vocabulary pattern: Students from {location} ({loc_type})")
                
                # Use proper column based on location type
                if loc_type == "city":
                    return f"""SELECT COUNT(DISTINCT s.StudentID) AS total 
                              FROM Students s WITH (NOLOCK) 
                              LEFT JOIN Cities c1 WITH (NOLOCK) ON s.CityIdPhysical = c1.CityID 
                              LEFT JOIN Cities c2 WITH (NOLOCK) ON s.CityIdPostal = c2.CityID 
                              WHERE c1.CityName COLLATE Latin1_General_CI_AI LIKE '%{location}%' 
                                 OR c2.CityName COLLATE Latin1_General_CI_AI LIKE '%{location}%'"""
                elif loc_type == "state":
                    return f"""SELECT COUNT(DISTINCT s.StudentID) AS total 
                              FROM Students s WITH (NOLOCK) 
                              LEFT JOIN States st1 WITH (NOLOCK) ON s.StateIdPhysical = st1.StateID 
                              LEFT JOIN States st2 WITH (NOLOCK) ON s.StateIdPostal = st2.StateID 
                              WHERE st1.StateName COLLATE Latin1_General_CI_AI LIKE '%{location}%' 
                                 OR st2.StateName COLLATE Latin1_General_CI_AI LIKE '%{location}%'"""
        
        # Pattern: Application status queries using enum values
        if "application" in prompt_lower and detected_enums.get("Status"):
            text, value = detected_enums["Status"]
            logger.info(f"🎯 Vocabulary pattern: Applications with status {text} (value={value})")
            return f"SELECT COUNT(*) AS total FROM ScholarshipApplications WITH (NOLOCK) WHERE Status = {value}"
        
        # Pattern: Document type queries using enum values
        if "document" in prompt_lower and detected_enums.get("DocumentType"):
            text, value = detected_enums["DocumentType"]
            logger.info(f"🎯 Vocabulary pattern: Documents of type {text} (value={value})")
            return f"SELECT COUNT(*) AS total FROM Documents WITH (NOLOCK) WHERE DocumentType = {value}"
        
        # Pattern: Family member queries using enum values
        if "family" in prompt_lower and detected_enums.get("Relationship"):
            text, value = detected_enums["Relationship"]
            logger.info(f"🎯 Vocabulary pattern: Family members with relationship {text} (value={value})")
            return f"SELECT COUNT(*) AS total FROM FamilyMembers WITH (NOLOCK) WHERE Relationship = {value}"
        
        return None
    
    def _generate_fallback_patterns(self, prompt_lower: str, original_prompt: str = None) -> Optional[str]:
        """Generate common patterns without requiring full schema analysis"""
        
        # Pattern: Age-based queries (calculate from DateOfBirth)
        if "student" in prompt_lower and ("age" in prompt_lower or "older" in prompt_lower or "younger" in prompt_lower):
            numbers = re.findall(r'\d+', prompt_lower)
            if numbers:
                age = numbers[0]
                
                # Check for greater than operations (older than)
                if any(op in prompt_lower for op in ["older than", "age greater", "age more", "age >", "age above"]):
                    logger.info(f"🎯 Fallback pattern: Students older than {age}")
                    return f"""SELECT COUNT(*) AS total 
                              FROM Students WITH (NOLOCK) 
                              WHERE DATEDIFF(YEAR, DateOfBirth, GETDATE()) > {age}"""
                
                # Check for less than operations (younger than)
                elif any(op in prompt_lower for op in ["younger than", "age less", "age fewer", "age <", "age under"]):
                    logger.info(f"🎯 Fallback pattern: Students younger than {age}")
                    return f"""SELECT COUNT(*) AS total 
                              FROM Students WITH (NOLOCK) 
                              WHERE DATEDIFF(YEAR, DateOfBirth, GETDATE()) < {age}"""
                
                # Check for exact age match (must be last to not catch "older than" or "younger than")
                elif "with age" in prompt_lower or "age is" in prompt_lower or f"age {age}" in prompt_lower:
                    logger.info(f"🎯 Fallback pattern: Students with age {age}")
                    # Calculate age using DATEDIFF from DateOfBirth
                    return f"""SELECT COUNT(*) AS total 
                              FROM Students WITH (NOLOCK) 
                              WHERE DATEDIFF(YEAR, DateOfBirth, GETDATE()) = {age}"""
        
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
                
                # Handle normalized Cities table structure with accent-insensitive matching
                # Students can be linked via CityIdPhysical or CityIdPostal
                # Using COLLATE Latin1_General_CI_AI for accent-insensitive comparison
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK) 
                          LEFT JOIN Cities c1 WITH (NOLOCK) ON s.CityIdPhysical = c1.Id 
                          LEFT JOIN Cities c2 WITH (NOLOCK) ON s.CityIdPostal = c2.Id 
                          WHERE c1.Name COLLATE Latin1_General_CI_AI LIKE '%{location}%' 
                             OR c2.Name COLLATE Latin1_General_CI_AI LIKE '%{location}%'"""
        
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
        
        # Pattern: Identification number queries (ID number, not SSN)
        # Also handles common typos like "stdent" instead of "student"
        if any(student_word in prompt_lower for student_word in ["student", "stdent", "studet", "studnt"]) and any(id_word in prompt_lower for id_word in ["identification number", "identification", "id number", "ident"]):
            # Check for specific ID number value
            # Look for alphanumeric patterns that could be ID numbers
            id_patterns = re.findall(r'\b[A-Z0-9]{6,15}\b', original_prompt or prompt_lower.upper())
            if id_patterns:
                id_value = id_patterns[0]
                logger.info(f"🎯 Pattern: Students with specific identification number {id_value}")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE IdentificationNumber = '{id_value}'"
            elif "without" in prompt_lower or "no " in prompt_lower or "missing" in prompt_lower:
                logger.info(f"🎯 Pattern: Students WITHOUT identification number")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE IdentificationNumber IS NULL OR IdentificationNumber = ''"
            else:
                logger.info(f"🎯 Pattern: Students WITH identification number")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE IdentificationNumber IS NOT NULL AND IdentificationNumber != ''"
        
        # Pattern: Social Security Number (SSN) queries
        if "student" in prompt_lower and any(ssn_word in prompt_lower for ssn_word in ["ssn", "social security", "social security number"]):
            # Check for specific SSN value (like 000-00-0000 or 000000000)
            # Look for pattern with digits and optional dashes
            ssn_pattern = re.findall(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b', prompt_lower)
            if ssn_pattern:
                ssn_value = ssn_pattern[0]
                logger.info(f"🎯 Pattern: Students with specific SSN {ssn_value}")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE SSN = '{ssn_value}'"
            elif "without" in prompt_lower or "no " in prompt_lower or "missing" in prompt_lower:
                logger.info(f"🎯 Pattern: Students WITHOUT SSN")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE SSN IS NULL OR SSN = ''"
            else:
                logger.info(f"🎯 Pattern: Students WITH SSN")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE SSN IS NOT NULL AND SSN != ''"
        
        # Pattern: Mobile Phone queries  
        if "student" in prompt_lower and any(phone_word in prompt_lower for phone_word in ["mobile phone", "mobile", "cell phone", "cell"]):
            if "without" in prompt_lower or "no " in prompt_lower or "missing" in prompt_lower:
                logger.info(f"🎯 Pattern: Students WITHOUT mobile phone")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE MobilePhone IS NULL OR MobilePhone = ''"
            else:
                logger.info(f"🎯 Pattern: Students WITH mobile phone")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE MobilePhone IS NOT NULL AND MobilePhone != ''"
        
        # Pattern: Home Phone queries
        if "student" in prompt_lower and "home phone" in prompt_lower:
            if "without" in prompt_lower or "no " in prompt_lower or "missing" in prompt_lower:
                logger.info(f"🎯 Pattern: Students WITHOUT home phone")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE HomePhone IS NULL OR HomePhone = ''"
            else:
                logger.info(f"🎯 Pattern: Students WITH home phone")
                return f"SELECT COUNT(*) AS total FROM Students WITH (NOLOCK) WHERE HomePhone IS NOT NULL AND HomePhone != ''"
        
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

    def _enhance_query_with_metadata(self, base_query: str, prompt: str, schema_info: Dict[str, Any], connection_id: int = 1) -> str:
        """Enhance query using indexes, relationships, and enums for better performance"""
        try:
            logger.info("🔧 Enhancing query with metadata (indexes, relationships, enums)")
            
            # Get schema analysis
            schema_analysis = self._analyze_schema_relationships(schema_info)
            indexed_cols = schema_analysis.get("indexed_columns", {})
            relationships = schema_analysis.get("relationships", {})
            primary_keys = schema_analysis.get("primary_keys", {})
            
            # Log available optimization metadata
            if indexed_cols:
                logger.info(f"📊 Available indexes: {list(indexed_cols.keys())[:5]} tables have indexes")
            if relationships:
                logger.info(f"🔗 Available relationships: {len(relationships)} foreign keys found")
            if primary_keys:
                logger.info(f"🔑 Primary keys available for: {list(primary_keys.keys())[:5]}")
            
            # Check if WHERE clause uses indexed columns
            if "WHERE" in base_query.upper():
                where_match = re.search(r'WHERE\s+(.+?)(?:ORDER BY|GROUP BY|HAVING|$)', base_query, re.IGNORECASE | re.DOTALL)
                if where_match:
                    where_clause = where_match.group(1)
                    
                    # Check each table's indexed columns
                    for table_name, idx_cols in indexed_cols.items():
                        if table_name in base_query:
                            for col in idx_cols:
                                if col in where_clause:
                                    logger.info(f"✅ Query uses indexed column: {table_name}.{col} - good for performance!")
                                    
            # Suggest JOIN optimization based on relationships
            if "students" in prompt.lower() and "applications" in prompt.lower():
                if "Students.Id" in relationships or any("StudentId" in k for k in relationships.keys()):
                    logger.info("💡 Using foreign key relationship for Students-Applications JOIN")
                    
            # Use enum mappings if available
            if hasattr(self, '_load_enum_mappings'):
                try:
                    enum_mappings = self._load_enum_mappings(connection_id)
                    if enum_mappings:
                        # Replace text values with enum numeric values
                        for enum_name, values in enum_mappings.items():
                            for text_val, num_val in values.items():
                                if text_val.lower() in prompt.lower():
                                    # Replace in query
                                    base_query = re.sub(
                                        rf"=\s*['\"]?{re.escape(text_val)}['\"]?",
                                        f"= {num_val}",
                                        base_query,
                                        flags=re.IGNORECASE
                                    )
                                    logger.info(f"📊 Enum optimization: {text_val} -> {num_val} ({enum_name})")
                except Exception as e:
                    logger.debug(f"Could not load enums: {e}")
                    
            return base_query
            
        except Exception as e:
            logger.warning(f"Could not enhance query with metadata: {e}")
            return base_query
    
    def _pattern_match_sql(self, prompt: str, schema_info: Dict[str, Any], connection_id: int = 1) -> Optional[str]:
        """Enhanced pattern matching with schema awareness and column intelligence"""
        prompt_lower = prompt.lower().strip()
        logger.info(f"🔍 Pattern matching called for: '{prompt}' (connection: {connection_id})")
        
        # Analyze schema for smart query generation
        schema_analysis = self._analyze_schema_relationships(schema_info)
        
        # Use column intelligence if available
        semantic_analysis = None
        if self.column_intelligence and schema_info:
            semantic_analysis = self.column_intelligence.analyze_column_semantics(schema_info)
            
            # Try location-aware query generation first
            location_query = self.column_intelligence.generate_location_aware_query(
                prompt, semantic_analysis, schema_info)
            if location_query:
                logger.info("🎯 Column Intelligence: Generated location-aware query")
                # Enhance with metadata before returning
                return self._enhance_query_with_metadata(location_query, prompt, schema_info, connection_id)
        
        # Try vocabulary-based query generation (NEW)
        vocabulary_result = self._generate_vocabulary_based_query(prompt_lower, prompt)
        if vocabulary_result:
            logger.info("🎯 Vocabulary Service: Generated query using database vocabulary")
            return self._generate_index_optimized_query(vocabulary_result, "Students", schema_analysis)
        
        # Load dynamic enum mappings
        enum_mappings = self._load_enum_mappings(connection_id)
        status_mappings = enum_mappings.get("application_status", {})
        
        # Try dynamic patterns first (even with limited schema)
        dynamic_result = self._generate_dynamic_patterns(prompt_lower, schema_analysis, prompt, semantic_analysis)
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
                    logger.info(f"🎯 Priority pattern: Students from {location} (normalized Cities table with accent-insensitive)")
                    
                    # Use normalized Cities table with both physical and postal addresses
                    # Using COLLATE for accent-insensitive comparison (handles Bayamón, San Sebastián, etc.)
                    return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                              FROM Students s WITH (NOLOCK) 
                              LEFT JOIN Cities c1 WITH (NOLOCK) ON s.CityIdPhysical = c1.Id 
                              LEFT JOIN Cities c2 WITH (NOLOCK) ON s.CityIdPostal = c2.Id 
                              WHERE c1.Name COLLATE Latin1_General_CI_AI LIKE '%{location}%' 
                                 OR c2.Name COLLATE Latin1_General_CI_AI LIKE '%{location}%'"""
        
        # HIGH PRIORITY: Family member patterns (must come before fallback patterns to avoid "member" conflicts)
        if ("count" in prompt_lower and "student" in prompt_lower and 
            any(word in prompt_lower for word in ["family", "familiy", "familymember"]) and 
            any(word in prompt_lower for word in ["member", "members"])):
            # Extract the number from the prompt
            numbers = re.findall(r'\d+', prompt_lower)
            threshold = int(numbers[0]) if numbers else 1
            
            # Check for "more than", "or more", "greater than" or ">" or "then" (common typo for "than")
            if any(phrase in prompt_lower for phrase in ["more than", "more then", "or more", "or greater", "greater than", "greater then", ">", "over"]):
                logger.info(f"🎯 HIGH PRIORITY Pattern: count students with more than {threshold} family members (using JOIN)")
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
                logger.info(f"🎯 HIGH PRIORITY Pattern: count students with less than {threshold} family members (using JOIN)")
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
                logger.info(f"🎯 HIGH PRIORITY Pattern: count students with exactly {threshold} family members (using JOIN)")
                return f"""SELECT COUNT(DISTINCT s.Id) AS total 
                          FROM Students s WITH (NOLOCK) 
                          INNER JOIN (
                              SELECT StudentId, COUNT(*) as family_count 
                              FROM FamilyMembers WITH (NOLOCK) 
                              GROUP BY StudentId 
                              HAVING COUNT(*) = {threshold}
                          ) fm ON s.Id = fm.StudentId"""
        
        # Fallback dynamic patterns without schema dependency
        fallback_result = self._generate_fallback_patterns(prompt_lower, prompt)
        if fallback_result:
            return fallback_result
        
        # Pattern: count students by application status with totals
        if "count" in prompt_lower and ("student" in prompt_lower or "students" in prompt_lower) and ("status" in prompt_lower or "application" in prompt_lower) and any(word in prompt_lower for word in ["group", "by", "each", "breakdown", "total"]):
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
        # Handle both singular "student" and plural "students"
        logger.info(f"🔍 Checking for status pattern. Status mappings: {status_mappings}")
        logger.info(f"🔍 Status keys in prompt? {[status for status in status_mappings.keys() if status in prompt_lower]}")
        
        if "count" in prompt_lower and ("student" in prompt_lower or "students" in prompt_lower) and "application" in prompt_lower and any(status in prompt_lower for status in status_mappings.keys()):
            logger.info(f"✅ Status pattern conditions met!")
            for status_text, status_value in status_mappings.items():
                if status_text in prompt_lower:
                    logger.info(f"🎯 Pattern matched: count students with application status {status_text} (value={status_value})")
                    return f"SELECT COUNT(DISTINCT s.Id) AS total FROM Students s WITH (NOLOCK) INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId WHERE sa.Status = {status_value}"
        
        # Pattern: count students with applications (any status)
        if "count" in prompt_lower and ("student" in prompt_lower or "students" in prompt_lower) and "application" in prompt_lower:
            logger.info("🎯 Pattern matched: count students with applications")
            return "SELECT COUNT(DISTINCT s.Id) AS total FROM Students s WITH (NOLOCK) INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId"
        
        # Pattern: show students with specific application status
        if "show" in prompt_lower and ("student" in prompt_lower or "students" in prompt_lower) and "application" in prompt_lower and any(status in prompt_lower for status in status_mappings.keys()):
            # Try to extract a number from the prompt
            numbers = re.findall(r'\d+', prompt_lower)
            limit = int(numbers[0]) if numbers else 100
            
            for status_text, status_value in status_mappings.items():
                if status_text in prompt_lower:
                    logger.info(f"🎯 Pattern matched: show {limit} students with application status {status_text}")
                    return f"SELECT TOP {limit} s.*, sa.Status FROM Students s WITH (NOLOCK) INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId WHERE sa.Status = {status_value}"
        
        # Pattern: show N students (e.g., "show 5 students", "show first 10 students")
        if ("show" in prompt_lower or "first" in prompt_lower or "top" in prompt_lower) and ("student" in prompt_lower or "students" in prompt_lower) and "application" not in prompt_lower:
            # Try to extract a number from the prompt
            numbers = re.findall(r'\d+', prompt_lower)
            if numbers:
                limit = int(numbers[0])
                logger.info(f"🎯 Pattern matched: show {limit} students")
                return f"SELECT TOP {limit} * FROM Students WITH (NOLOCK)"
            else:
                logger.info("🎯 Pattern matched: show students (default 100)")
                return "SELECT TOP 100 * FROM Students WITH (NOLOCK)"
        
        
        # Check for StudentRecommendeds FIRST before generic detection
        if "count" in prompt_lower and ("student" in prompt_lower or "students" in prompt_lower) and ("recommended" in prompt_lower or "recommendeds" in prompt_lower):
            logger.info("🎯 Pattern matched: count student recommendeds")
            return "SELECT COUNT(*) AS total FROM StudentRecommendeds WITH (NOLOCK)"
        
        # Check for ScholarshipApplications BEFORE generic detection (use plural - has data)
        if "count" in prompt_lower and (("scholarship" in prompt_lower and "application" in prompt_lower) or "scholarshipapplication" in prompt_lower):
            logger.info("🎯 Pattern matched: count scholarship applications (using ScholarshipApplications plural)")
            return "SELECT COUNT(*) AS total FROM ScholarshipApplications WITH (NOLOCK)"
        
        # Generic table count detection - check for table names in the prompt
        if "count" in prompt_lower and schema_info and "tables" in schema_info:
            # Identify standalone/irrelevant tables to skip
            standalone_tables = self._identify_standalone_tables(schema_info)
            
            # Check each table name against the prompt
            for table_name in schema_info.get("tables", {}).keys():
                # Skip standalone tables unless explicitly mentioned
                if table_name in standalone_tables:
                    # Only match if table is explicitly named in prompt
                    if table_name.lower() not in prompt_lower:
                        continue
                table_lower = table_name.lower()
                
                # Create variations for matching
                table_variations = []
                
                # Add exact lowercase match
                table_variations.append(table_lower)
                
                # Add singular/plural variations
                table_variations.append(table_lower.rstrip('s'))  # singular
                table_variations.append(table_lower + 's')  # plural
                
                # Handle CamelCase table names by adding space-separated version
                # e.g., "ScholarshipApplications" -> "scholarship applications"
                camel_case_split = re.sub(r'([A-Z])', r' \1', table_name).strip().lower()
                if ' ' in camel_case_split:  # Only add if it actually splits into multiple words
                    table_variations.append(camel_case_split)
                    # Also add singular version of the split
                    table_variations.append(camel_case_split.rstrip('s'))
                
                # Also handle compound words without case changes
                # e.g., "StudentRecommendeds" -> "student recommendeds"
                if any(c.isupper() for c in table_name[1:]):  # Has internal uppercase letters
                    # Try splitting on capital letters
                    words = re.findall('[A-Z][a-z]*', table_name)
                    if words:
                        space_version = ' '.join(words).lower()
                        table_variations.append(space_version)
                        table_variations.append(space_version.rstrip('s'))
                
                # Remove duplicates while preserving order
                seen = set()
                unique_variations = []
                for v in table_variations:
                    if v not in seen and len(v) > 2:  # Avoid very short strings
                        seen.add(v)
                        unique_variations.append(v)
                
                for variation in unique_variations:
                    if variation in prompt_lower:
                        # Special case: ScholarshipApplication vs ScholarshipApplications - prefer plural (has data)
                        if table_name == "ScholarshipApplication" and "scholarship" in prompt_lower and "application" in prompt_lower:
                            # Skip singular, let plural match instead
                            continue
                        
                        # Special case: StudentRecommendeds should match if "recommendeds" is mentioned
                        if table_name == "StudentRecommendeds" and ("recommended" in prompt_lower or "recommendeds" in prompt_lower):
                            logger.info(f"🎯 Generic pattern matched: count {table_name} (matched: '{variation}')")
                            return f"SELECT COUNT(*) AS total FROM {table_name} WITH (NOLOCK)"
                        
                        # Don't match Students table unless ONLY "student" is mentioned (not "student recommended")
                        if table_name == "Students":
                            if "student" not in prompt_lower or "recommended" in prompt_lower:
                                continue
                        
                        # For other tables, don't match if "student" is in the prompt but table isn't student-related
                        if "student" in prompt_lower and not table_name.startswith("Student"):
                            continue
                        
                        logger.info(f"🎯 Generic pattern matched: count {table_name} (matched: '{variation}')")
                        return f"SELECT COUNT(*) AS total FROM {table_name} WITH (NOLOCK)"
        
        # Specific patterns for common tables (fallback if schema not available)
        if "count" in prompt_lower:
            if ("cities" in prompt_lower or "city" in prompt_lower) and "student" not in prompt_lower:
                logger.info("🎯 Pattern matched: count cities")
                return "SELECT COUNT(*) AS total FROM Cities WITH (NOLOCK)"
            
            if ("highschools" in prompt_lower or "high schools" in prompt_lower or "school" in prompt_lower) and "student" not in prompt_lower:
                logger.info("🎯 Pattern matched: count highschools")
                return "SELECT COUNT(*) AS total FROM HighSchools WITH (NOLOCK)"
            
            if ("regions" in prompt_lower or "region" in prompt_lower) and "student" not in prompt_lower:
                logger.info("🎯 Pattern matched: count regions")
                return "SELECT COUNT(*) AS total FROM Regions WITH (NOLOCK)"
            
            if ("occupation" in prompt_lower) and "student" not in prompt_lower:
                logger.info("🎯 Pattern matched: count occupations")
                return "SELECT COUNT(*) AS total FROM Occupations WITH (NOLOCK)"
            
            if ("municipio" in prompt_lower) and "student" not in prompt_lower:
                logger.info("🎯 Pattern matched: count municipios")
                return "SELECT COUNT(*) AS total FROM Municipios WITH (NOLOCK)"
            
            if ("family" in prompt_lower and "member" in prompt_lower) and "student" not in prompt_lower:
                logger.info("🎯 Pattern matched: count family members")
                return "SELECT COUNT(*) AS total FROM FamilyMembers WITH (NOLOCK)"
            
            # Check for StudentRecommendeds BEFORE checking for just Students
            if "student" in prompt_lower and ("recommended" in prompt_lower or "recommendeds" in prompt_lower):
                logger.info("🎯 Pattern matched: count student recommendeds")
                return "SELECT COUNT(*) AS total FROM StudentRecommendeds WITH (NOLOCK)"
            
            # Check for students with specific criteria BEFORE generic student count
            # This prevents "count students with X" from matching the generic pattern
            if "student" in prompt_lower and " with " in prompt_lower:
                # Don't match here - let it fall through to more specific patterns
                pass
            # Only match Students if "student" is explicitly mentioned and not recommendeds
            elif "student" in prompt_lower and "application" not in prompt_lower and "recommended" not in prompt_lower:
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
            # Check if the prompt is already raw SQL
            prompt_upper = prompt.strip().upper()
            if any(prompt_upper.startswith(keyword) for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']):
                logger.info("🎯 OptimizedRAG: Raw SQL detected, passing through directly")
                metadata.update({
                    "method": "raw_sql_passthrough",
                    "result_type": "table"
                })
                return prompt.strip(), metadata
            
            # Step 1: Fast pattern matching (< 1ms)
            pattern_start = time.time()
            pattern_sql = self._pattern_match_sql(prompt, schema_info or {}, connection_id or 1)
            pattern_time = time.time() - pattern_start
            
            if pattern_sql:
                # Apply query optimization to pattern-matched SQL too
                optimization_start = time.time()
                try:
                    # Prepare schema info for optimizer
                    optimizer_schema = {
                        "tables": schema_info.get("tables", {}) if schema_info else {},
                        "indexes": self.db_metadata.get("indexes", {}),
                        "foreign_keys": self.db_metadata.get("foreign_keys", {}),
                        "table_stats": self.db_metadata.get("table_stats", {})
                    }
                    
                    # Optimize the pattern-matched query
                    optimized_sql, optimization_metadata = query_optimizer.optimize_query(
                        pattern_sql,
                        optimizer_schema,
                        query_stats=None
                    )
                    
                    # Use optimized query if available
                    if optimized_sql:
                        pattern_sql = optimized_sql
                        metadata["optimization"] = optimization_metadata
                        logger.info(f"⚡ OptimizedRAG: Pattern query optimized with {len(optimization_metadata.get('optimizations', []))} improvements")
                    
                except Exception as opt_error:
                    logger.warning(f"⚠️ OptimizedRAG: Pattern optimization failed, using original: {str(opt_error)}")
                    metadata["optimization_error"] = str(opt_error)
                
                optimization_time = time.time() - optimization_start
                
                metadata.update({
                    "method": "pattern_matching",
                    "pattern_match_time": f"{pattern_time*1000:.2f}ms",
                    "optimization_time": f"{optimization_time*1000:.2f}ms",
                    "result_type": "table"
                })
                total_time = time.time() - start_time
                logger.info(f"✅ OptimizedRAG: Pattern match completed in {total_time*1000:.2f}ms")
                return pattern_sql, metadata
            
            # Step 2: LLM generation with optimized prompt
            if not self.llm:
                logger.warning("⚠️ OptimizedRAG: No LLM available, cannot generate SQL without pattern match")
                metadata.update({
                    "method": "no_llm_error",
                    "error": "No LLM available and no pattern matched",
                    "result_type": "error"
                })
                return None, metadata
            
            # Build optimized context with connection_id for enum support
            context_start = time.time()
            schema_context = self._build_optimized_schema_context(schema_info or {}, connection_id)
            context_time = time.time() - context_start
            
            # Enhanced prompt template using full metadata
            system_prompt = """You are an expert MSSQL query generator with full database schema knowledge.

CRITICAL RULES:
1. Generate ONLY the SQL query - no explanations or markdown
2. Use the EXACT table and column names from the schema
3. Use proper JOINs based on the foreign key relationships provided
4. Always add WITH (NOLOCK) for SELECT queries
5. Use indexes when available for better performance
6. Primary keys are optimal for DISTINCT operations
7. For ENUM columns, ALWAYS use numeric values (e.g., Status = 3), NEVER string values

IMPORTANT PATTERNS:
- "count X" → SELECT COUNT(*) FROM X WITH (NOLOCK)
- "count X with Y" → JOIN tables using foreign keys, COUNT DISTINCT on primary key
- "show X with Y" → SELECT with JOIN using foreign key relationships
- "X by Y" → GROUP BY Y column
- "active X" → WHERE IsActive = 1 (check for IsActive column)

LOCATION QUERIES:
- "students from [city]" → JOIN Students with Cities table using CityIdPhysical or CityIdPostal
- Use CityIdPhysical for physical location queries
- Use CityIdPostal for mailing address queries
- When location type not specified, check both CityIdPhysical and CityIdPostal
- Cities are normalized - always JOIN with Cities table to get city names

COLUMN UNDERSTANDING:
- Pay attention to column semantics in the schema
- Location columns ending in "Physical" refer to where someone lives
- Location columns ending in "Postal" refer to mailing address
- Columns with "Id" suffix usually reference other tables
- Use semantic information to understand what columns mean

{schema_context}

Generate SQL for: {prompt}

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
            
            # Apply query optimization
            optimization_start = time.time()
            try:
                # Prepare schema info for optimizer
                optimizer_schema = {
                    "tables": table_info,
                    "indexes": self.db_metadata.get("indexes", {}),
                    "foreign_keys": self.db_metadata.get("foreign_keys", {}),
                    "table_stats": self.db_metadata.get("table_stats", {})
                }
                
                # Optimize the generated query
                optimized_sql, optimization_metadata = query_optimizer.optimize_query(
                    sql_query,
                    optimizer_schema,
                    query_stats=metadata.get("query_stats")
                )
                
                # Use optimized query if available
                if optimized_sql:
                    sql_query = optimized_sql
                    metadata["optimization"] = optimization_metadata
                    logger.info(f"⚡ OptimizedRAG: Query optimized with {len(optimization_metadata.get('optimizations', []))} improvements")
                
            except Exception as opt_error:
                logger.warning(f"⚠️ OptimizedRAG: Optimization failed, using original query: {str(opt_error)}")
                metadata["optimization_error"] = str(opt_error)
            
            optimization_time = time.time() - optimization_start
            total_time = time.time() - start_time
            
            metadata.update({
                "method": "llm_optimized",
                "context_time": f"{context_time*1000:.2f}ms",
                "llm_time": f"{llm_time*1000:.2f}ms",
                "optimization_time": f"{optimization_time*1000:.2f}ms",
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
            
            # Return error instead of defaulting to Students
            metadata.update({
                "method": "error",
                "error": str(e),
                "error_time": f"{error_time*1000:.2f}ms",
                "result_type": "error"
            })
            return None, metadata
    
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