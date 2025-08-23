from typing import Optional, Tuple, Dict, Any, List
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json
import hashlib
import logging
from ..config import settings
from .schema_analyzer import SchemaAnalyzer
from .enum_service import enum_service

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.llm = None
        self.schema_analyzer = SchemaAnalyzer()
        self.redis_service = None
        if settings.openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                    temperature=0.1
                )
                print("OpenAI ChatGPT initialized successfully")
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")
                self.llm = None
    
    def set_redis_service(self, redis_service):
        """Set Redis service for caching"""
        self.redis_service = redis_service
    
    async def generate_sql_with_full_context(self, prompt: str, comprehensive_context: Dict[str, Any], connection_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL with comprehensive context including schema, enums, and documentation"""
        
        # Extract components from comprehensive context
        schema_info = comprehensive_context.get("schema_info")
        enums = comprehensive_context.get("enums")
        documentation = comprehensive_context.get("documentation")
        
        # Check Redis cache for cached SQL
        if self.redis_service and self.redis_service.is_connected and connection_id:
            cached_sql = await self.redis_service.get_cached_sql(prompt, connection_id)
            if cached_sql:
                logger.info(f"SQL loaded from Redis cache for prompt: {prompt[:50]}...")
                return cached_sql, {"cached": True}
        
        if not self.llm:
            # Fallback to enhanced pattern matching with full context
            sql, metadata = await self._comprehensive_sql_generation(prompt, comprehensive_context, connection_id)
            
            # Cache the result if successful
            if sql and self.redis_service and self.redis_service.is_connected and connection_id:
                await self.redis_service.cache_sql_generation(
                    prompt, connection_id, sql, 
                    ttl=settings.cache_ttl_sql
                )
            
            return sql, metadata
        
        # Enhanced system prompt with comprehensive context
        system_prompt = """You are a SQL expert assistant with COMPLETE database knowledge. Convert natural language queries to valid MSSQL queries using ALL available context.

        MSSQL-Specific Syntax Rules:
        1. Use TOP instead of LIMIT (e.g., SELECT TOP 10 * FROM table)
        2. Use OFFSET/FETCH for pagination: OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY
        3. Use [] for identifiers with spaces or reserved words
        4. String concatenation: Use + operator (e.g., FirstName + ' ' + LastName)
        5. Date functions: GETDATE(), DATEADD(), DATEDIFF()
        6. Use ISNULL() or COALESCE() for null handling
        7. Use WITH (NOLOCK) for read-only queries for better performance

        JOIN Syntax & Relationships:
        - INNER JOIN: Returns matching rows from both tables
        - LEFT JOIN: Returns all rows from left table
        - Use foreign key relationships from documentation
        - Consider table relationships when joining

        AVAILABLE DATABASE CONTEXT:
        {schema_context}

        ENUM VALUES AND MAPPINGS:
        {enum_context}

        TABLE RELATIONSHIPS AND DOCUMENTATION:
        {documentation_context}

        IMPORTANT INSTRUCTIONS:
        1. ALWAYS use the exact table names and column names from the schema
        2. ALWAYS use the correct enum numeric values when filtering by status
        3. ALWAYS consider relationships between tables from the documentation
        4. Use appropriate JOINs based on foreign key relationships
        5. For ID columns that reference other tables, include descriptive names when possible
        6. Use meaningful aliases and column names in results
        7. Optimize queries with appropriate indexing hints

        Output format:
        - Generate complete, executable MSSQL queries
        - Include proper JOINs based on relationships
        - Use correct enum values for filtering
        - Return ONLY the SQL query, no explanations
        """
        
        # Build comprehensive schema context
        schema_context = ""
        if schema_info and "tables" in schema_info:
            table_list = list(schema_info["tables"].keys())
            schema_context = f"Available tables: {', '.join(table_list)}\n\n"
            
            # Add detailed schema with relationships
            for table_name, table_info in schema_info["tables"].items():
                if table_info.get("columns"):
                    columns = []
                    for col in table_info["columns"][:25]:  # Include more columns
                        col_desc = f"{col['name']} ({col['data_type']}"
                        if not col.get('nullable', True):
                            col_desc += ", NOT NULL"
                        col_desc += ")"
                        columns.append(col_desc)
                    
                    schema_context += f"Table {table_name}:\n"
                    schema_context += f"  Columns: {', '.join(columns)}\n"
                    
                    # Add primary keys
                    if table_info.get("primary_keys"):
                        schema_context += f"  Primary Keys: {', '.join(table_info['primary_keys'])}\n"
                    
                    # Add foreign keys
                    if table_info.get("foreign_keys"):
                        fk_list = []
                        for fk in table_info["foreign_keys"]:
                            fk_list.append(f"{fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}")
                        schema_context += f"  Foreign Keys: {', '.join(fk_list)}\n"
                    
                    if table_info.get("row_count"):
                        schema_context += f"  Row count: {table_info['row_count']}\n"
                    schema_context += "\n"
        
        # Build enum context with complete mappings
        enum_context = ""
        if enums and isinstance(enums, dict):
            enum_context = "Enum Value Mappings (use numeric values in queries):\n"
            for enum_type, values in enums.items():
                enum_context += f"\n{enum_type}:\n"
                if isinstance(values, list):
                    for value_info in values:
                        if isinstance(value_info, dict):
                            enum_context += f"  {value_info.get('value', 0)} = '{value_info.get('label', '')}' ({value_info.get('description', 'No description')})\n"
                elif isinstance(values, dict):
                    # Handle nested structure
                    for key, value_info in values.items():
                        if isinstance(value_info, dict):
                            enum_context += f"  {value_info.get('value', 0)} = '{key}' ({value_info.get('description', 'No description')})\n"
        
        # Build documentation context
        documentation_context = ""
        if documentation and 'error' not in documentation:
            if documentation.get("relationships"):
                relationships = documentation["relationships"]
                documentation_context += "Table Relationships:\n"
                if isinstance(relationships, list):
                    for rel in relationships:
                        documentation_context += f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']} ({rel['relationship_type']})\n"
                documentation_context += "\n"
            
            if documentation.get("tables"):
                tables = documentation["tables"]
                documentation_context += "Table Documentation:\n"
                if isinstance(tables, dict):
                    for table_name, table_doc in tables.items():
                        documentation_context += f"  {table_name}: {table_doc.get('description', 'No description')}\n"
                        if table_doc.get("columns"):
                            columns = table_doc["columns"]
                            if isinstance(columns, list):
                                # Handle list of column dictionaries
                                for col_info in columns:
                                    if isinstance(col_info, dict) and col_info.get("description"):
                                        documentation_context += f"    {col_info['name']}: {col_info['description']}\n"
                            elif isinstance(columns, dict):
                                # Handle dictionary of column name -> description
                                for col_name, col_desc in columns.items():
                                    if col_desc:
                                        documentation_context += f"    {col_name}: {col_desc}\n"
        
        messages = [
            SystemMessage(content=system_prompt.format(
                schema_context=schema_context,
                enum_context=enum_context,
                documentation_context=documentation_context
            )),
            HumanMessage(content=f"Convert this to SQL using ALL available context: {prompt}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            sql_query = response.content.strip()
            
            # Clean up the SQL query
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            # Determine result type
            result_type = self._determine_result_type(sql_query)
            
            # Cache the result if successful
            if sql_query and self.redis_service and self.redis_service.is_connected and connection_id:
                await self.redis_service.cache_sql_generation(
                    prompt, connection_id, sql_query, 
                    ttl=settings.cache_ttl_sql
                )
                logger.info(f"SQL cached in Redis for prompt: {prompt[:50]}...")
            
            return sql_query, {"result_type": result_type, "context_used": "comprehensive"}
        
        except Exception as e:
            return "", {"error": str(e), "result_type": "error"}

    async def generate_sql(self, prompt: str, schema_info: Optional[Dict[str, Any]] = None, connection_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL from natural language prompt using schema context and enums"""
        
        # Check Redis cache for cached SQL
        if self.redis_service and self.redis_service.is_connected and connection_id:
            cached_sql = await self.redis_service.get_cached_sql(prompt, connection_id)
            if cached_sql:
                logger.info(f"SQL loaded from Redis cache for prompt: {prompt[:50]}...")
                return cached_sql, {"cached": True}
        
        if not self.llm:
            # Fallback to pattern matching with schema awareness
            sql, metadata = await self._schema_aware_sql_generation(prompt, schema_info, connection_id)
            
            # Cache the result if successful
            if sql and self.redis_service and self.redis_service.is_connected and connection_id:
                await self.redis_service.cache_sql_generation(
                    prompt, connection_id, sql, 
                    ttl=settings.cache_ttl_sql
                )
            
            return sql, metadata
        
        system_prompt = """You are a SQL expert assistant. Convert natural language queries to valid MSSQL queries.
        
        MSSQL-Specific Syntax Rules:
        1. Use TOP instead of LIMIT (e.g., SELECT TOP 10 * FROM table)
        2. Use OFFSET/FETCH for pagination: OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY
        3. Use [] for identifiers with spaces or reserved words
        4. String concatenation: Use + operator (e.g., FirstName + ' ' + LastName)
        5. Date functions: GETDATE(), DATEADD(), DATEDIFF()
        6. Use ISNULL() or COALESCE() for null handling
        
        JOIN Syntax:
        - INNER JOIN: Returns matching rows from both tables
        - LEFT JOIN: Returns all rows from left table
        - RIGHT JOIN: Returns all rows from right table
        - FULL OUTER JOIN: Returns all rows from both tables
        - CROSS JOIN: Cartesian product of tables
        
        Query Optimization:
        - Use WITH (NOLOCK) for read-only queries
        - Include appropriate indexes in WHERE clauses
        - Use EXISTS instead of IN for better performance
        - Consider using CTEs for complex queries
        
        {schema_info}
        
        Output format:
        - If the result should be a table, generate a SELECT query
        - If the result is a single value or message, still use SELECT but indicate it's text
        - Always validate the SQL syntax
        - Return ONLY the SQL query, no explanations
        """
        
        # Format schema context for better LLM understanding
        schema_context = ""
        if schema_info and "tables" in schema_info:
            table_list = list(schema_info["tables"].keys())
            schema_context = f"Available tables: {', '.join(table_list)}\n\n"
            
            # Add detailed schema for each table (limit to relevant tables)
            for table_name, table_info in list(schema_info["tables"].items())[:10]:  # Limit to 10 tables
                if table_info.get("columns"):
                    columns = [f"{col['name']} ({col['data_type']})" for col in table_info["columns"][:20]]  # Limit columns
                    schema_context += f"Table {table_name}:\n  Columns: {', '.join(columns)}\n"
                    if table_info.get("row_count"):
                        schema_context += f"  Row count: {table_info['row_count']}\n"
                    schema_context += "\n"
        
        # Add enum context if available
        if connection_id:
            enum_context = await enum_service.get_enum_context(connection_id)
            if enum_context:
                schema_context += f"\nEnum values:\n{enum_context}\n"
        
        messages = [
            SystemMessage(content=system_prompt.format(schema_info=schema_context)),
            HumanMessage(content=f"Convert this to SQL: {prompt}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            sql_query = response.content.strip()
            
            # Clean up the SQL query
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            # Determine result type
            result_type = self._determine_result_type(sql_query)
            
            # Cache the result if successful
            if sql_query and self.redis_service and self.redis_service.is_connected and connection_id:
                await self.redis_service.cache_sql_generation(
                    prompt, connection_id, sql_query, 
                    ttl=settings.cache_ttl_sql
                )
                logger.info(f"SQL cached in Redis for prompt: {prompt[:50]}...")
            
            return sql_query, {"result_type": result_type}
        
        except Exception as e:
            return "", {"error": str(e), "result_type": "error"}
    
    async def _comprehensive_sql_generation(self, prompt: str, comprehensive_context: Dict[str, Any], connection_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Enhanced SQL generation with comprehensive context (schema + enums + documentation)"""
        
        # Extract components
        schema_info = comprehensive_context.get("schema_info")
        enums = comprehensive_context.get("enums")
        documentation = comprehensive_context.get("documentation")
        
        prompt_lower = prompt.lower()
        
        # Enhanced pattern matching with comprehensive context
        if schema_info and "tables" in schema_info and schema_info["tables"]:
            relevant_tables = self.schema_analyzer.find_relevant_tables(prompt, schema_info)
            
            # Get relationships from documentation for intelligent JOINs
            relationships = {}
            if documentation and documentation.get("relationships"):
                for rel in documentation["relationships"]:
                    if rel["from_table"] not in relationships:
                        relationships[rel["from_table"]] = []
                    relationships[rel["from_table"]].append({
                        "to_table": rel["to_table"],
                        "from_column": rel["from_column"],
                        "to_column": rel["to_column"],
                        "type": rel["relationship_type"]
                    })
            
            # Enhanced patterns with comprehensive context awareness
            patterns = {
                r"show\s+tables?": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
                r"show\s+databases?": "SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name",
                r"describe\s+(\w+)": "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{}' ORDER BY ORDINAL_POSITION",
                
                # Enhanced enum-aware patterns
                r"approved|aprobada": lambda p, t, s: self._generate_comprehensive_enum_query(p, t, s, "ApplicationStatus", "Aprobada", comprehensive_context, connection_id),
                r"rejected|rechazada": lambda p, t, s: self._generate_comprehensive_enum_query(p, t, s, "ApplicationStatus", "Rechazada", comprehensive_context, connection_id),
                r"pending|evaluacion": lambda p, t, s: self._generate_comprehensive_enum_query(p, t, s, "ApplicationStatus", "En Evaluacion", comprehensive_context, connection_id),
                r"pagada|paid": lambda p, t, s: self._generate_comprehensive_enum_query(p, t, s, "PaymentStatus", "Pagada", comprehensive_context, connection_id),
                
                # Enhanced join patterns with relationship awareness
                r"student.*application|application.*student|students.*applications": lambda p, t, s: self._generate_comprehensive_join_query(p, t, s, ["Students", "Applications"], comprehensive_context, connection_id),
                r"student.*document|document.*student": lambda p, t, s: self._generate_comprehensive_join_query(p, t, s, ["Students", "Documents"], comprehensive_context, connection_id),
                r"application.*document|document.*application": lambda p, t, s: self._generate_comprehensive_join_query(p, t, s, ["Applications", "Documents"], comprehensive_context, connection_id),
                r"with\s+their|and\s+their|including": lambda p, t, s: self._generate_comprehensive_join_query(p, t, s, relevant_tables, comprehensive_context, connection_id),
                
                # Standard aggregation patterns
                r"how\s+many|count": lambda p, t, s: self._generate_comprehensive_count_query(p, t, s, comprehensive_context, connection_id),
                r"total": lambda p, t, s: self._generate_comprehensive_count_query(p, t, s, comprehensive_context, connection_id),
                r"number\s+of": lambda p, t, s: self._generate_comprehensive_count_query(p, t, s, comprehensive_context, connection_id),
                r"all|list|show\s+all": lambda p, t, s: self._generate_comprehensive_select_query(p, t, s, comprehensive_context, connection_id),
                r"average|avg": self._generate_avg_query,
                r"sum": self._generate_sum_query,
                r"max|maximum|highest": self._generate_max_query,
                r"min|minimum|lowest": self._generate_min_query,
            }
            
            for pattern, handler in patterns.items():
                if re.search(pattern, prompt_lower):
                    if callable(handler):
                        if handler.__name__.startswith('_generate_comprehensive'):
                            sql_query = handler(prompt_lower, relevant_tables, schema_info)
                        else:
                            sql_query = handler(prompt_lower, relevant_tables, schema_info)
                    else:
                        sql_query = handler
                    
                    if sql_query:
                        result_type = self._determine_result_type(sql_query)
                        return sql_query, {"result_type": result_type, "context_used": "comprehensive"}
        
        # Fallback to basic generation
        return self._basic_sql_generation(prompt)

    def _generate_comprehensive_enum_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any], 
                                         column_name: str, enum_value: str, comprehensive_context: Dict[str, Any], 
                                         connection_id: Optional[str]) -> str:
        """Generate enum query with comprehensive context"""
        
        # Get numeric value from enums
        numeric_value = None
        enums = comprehensive_context.get("enums", {})
        
        if isinstance(enums, dict):
            for enum_type, values in enums.items():
                if isinstance(values, list):
                    for value_info in values:
                        if isinstance(value_info, dict) and (value_info.get("label") == enum_value or enum_value in str(value_info.get("label", ""))):
                            numeric_value = value_info.get("value")
                            break
                elif isinstance(values, dict):
                    for key, value_info in values.items():
                        if isinstance(value_info, dict) and (key == enum_value or enum_value in key):
                            numeric_value = value_info.get("value")
                            break
                if numeric_value is not None:
                    break
        
        if not tables:
            return ""
        
        # Check if we need JOINs based on documentation relationships
        documentation = comprehensive_context.get("documentation", {})
        if self._needs_join_based_on_prompt(prompt, tables, documentation):
            return self._generate_comprehensive_join_query(prompt, tables, schema_info, tables, comprehensive_context, connection_id, enum_filter=(column_name, numeric_value))
        
        table = tables[0]
        
        if numeric_value is not None:
            if "count" in prompt.lower() or "how many" in prompt.lower():
                return f"SELECT COUNT(*) AS total FROM {table} WITH (NOLOCK) WHERE {column_name} = {numeric_value}"
            else:
                return f"SELECT TOP 100 * FROM {table} WITH (NOLOCK) WHERE {column_name} = {numeric_value}"
        
        return f"SELECT TOP 100 * FROM {table} WITH (NOLOCK)"

    def _generate_comprehensive_join_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any], 
                                         join_tables: List[str], comprehensive_context: Dict[str, Any], 
                                         connection_id: Optional[str], enum_filter: Optional[Tuple[str, int]] = None) -> str:
        """Generate JOIN query using comprehensive context with relationship information"""
        
        documentation = comprehensive_context.get("documentation", {})
        relationships = documentation.get("relationships", []) if documentation else []
        
        if not join_tables or len(join_tables) < 2:
            # Single table query
            if tables:
                table = tables[0]
                if enum_filter:
                    column_name, numeric_value = enum_filter
                    if "count" in prompt.lower():
                        return f"SELECT COUNT(*) AS total FROM {table} WITH (NOLOCK) WHERE {column_name} = {numeric_value}"
                    else:
                        return f"SELECT TOP 100 * FROM {table} WITH (NOLOCK) WHERE {column_name} = {numeric_value}"
                return f"SELECT TOP 100 * FROM {table} WITH (NOLOCK)"
            return ""
        
        # Build JOIN query using relationships from documentation
        main_table = join_tables[0]
        join_conditions = []
        joined_tables = [main_table]
        
        for target_table in join_tables[1:]:
            # Find relationship
            relationship = None
            for rel in relationships:
                if (rel["from_table"] == main_table and rel["to_table"] == target_table) or \
                   (rel["from_table"] == target_table and rel["to_table"] == main_table):
                    relationship = rel
                    break
            
            if relationship:
                if relationship["from_table"] == main_table:
                    join_condition = f"{main_table}.{relationship['from_column']} = {target_table}.{relationship['to_column']}"
                else:
                    join_condition = f"{main_table}.{relationship['to_column']} = {target_table}.{relationship['from_column']}"
                join_conditions.append(f"INNER JOIN {target_table} WITH (NOLOCK) ON {join_condition}")
                joined_tables.append(target_table)
        
        # Build query
        if "count" in prompt.lower():
            query = f"SELECT COUNT(*) AS total FROM {main_table} WITH (NOLOCK)"
        else:
            # Create meaningful column selection
            select_columns = []
            for table in joined_tables[:3]:  # Limit to 3 tables to avoid too wide results
                if table in schema_info.get("tables", {}):
                    # Select key columns
                    for col in schema_info["tables"][table]["columns"][:5]:  # Limit columns per table
                        select_columns.append(f"{table}.{col['name']}")
            
            if select_columns:
                query = f"SELECT {', '.join(select_columns)} FROM {main_table} WITH (NOLOCK)"
            else:
                query = f"SELECT * FROM {main_table} WITH (NOLOCK)"
        
        # Add JOINs
        for join_condition in join_conditions:
            query += f" {join_condition}"
        
        # Add enum filter if provided
        if enum_filter:
            column_name, numeric_value = enum_filter
            # Try to find which table has the status column
            status_table = main_table  # Default
            for table in joined_tables:
                if table in schema_info.get("tables", {}):
                    table_columns = [col["name"] for col in schema_info["tables"][table]["columns"]]
                    if column_name in table_columns:
                        status_table = table
                        break
            
            query += f" WHERE {status_table}.{column_name} = {numeric_value}"
        
        return query

    def _generate_comprehensive_count_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any], 
                                          comprehensive_context: Dict[str, Any], connection_id: Optional[str]) -> str:
        """Generate COUNT query with comprehensive context"""
        
        # Check for enum filters in prompt
        enums = comprehensive_context.get("enums", {})
        enum_filter = None
        
        if isinstance(enums, dict):
            for enum_type, values in enums.items():
                if isinstance(values, list):
                    for value_info in values:
                        if isinstance(value_info, dict) and str(value_info.get("label", "")).lower() in prompt.lower():
                            enum_filter = ("ApplicationStatus" if "Status" in enum_type else enum_type, value_info.get("value"))
                            break
                elif isinstance(values, dict):
                    for key, value_info in values.items():
                        if isinstance(value_info, dict) and key.lower() in prompt.lower():
                            enum_filter = ("ApplicationStatus" if "Status" in enum_type else enum_type, value_info.get("value"))
                            break
                if enum_filter:
                    break
        
        if not tables:
            return ""
        
        # Check if we need JOINs
        documentation = comprehensive_context.get("documentation", {})
        if self._needs_join_based_on_prompt(prompt, tables, documentation):
            # Find relevant tables for joining
            join_tables = self._find_join_tables_from_prompt(prompt, schema_info)
            if len(join_tables) > 1:
                return self._generate_comprehensive_join_query(prompt, tables, schema_info, join_tables, comprehensive_context, connection_id, enum_filter)
        
        table = tables[0]
        
        if enum_filter:
            column_name, numeric_value = enum_filter
            return f"SELECT COUNT(*) AS total FROM {table} WITH (NOLOCK) WHERE {column_name} = {numeric_value}"
        else:
            return f"SELECT COUNT(*) AS total FROM {table} WITH (NOLOCK)"

    def _generate_comprehensive_select_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any], 
                                           comprehensive_context: Dict[str, Any], connection_id: Optional[str]) -> str:
        """Generate SELECT query with comprehensive context"""
        
        if not tables:
            return ""
        
        # Check if we need JOINs
        documentation = comprehensive_context.get("documentation", {})
        if self._needs_join_based_on_prompt(prompt, tables, documentation):
            join_tables = self._find_join_tables_from_prompt(prompt, schema_info)
            if len(join_tables) > 1:
                return self._generate_comprehensive_join_query(prompt, tables, schema_info, join_tables, comprehensive_context, connection_id)
        
        table = tables[0]
        return f"SELECT TOP 100 * FROM {table} WITH (NOLOCK)"

    def _needs_join_based_on_prompt(self, prompt: str, tables: List[str], documentation: Dict[str, Any]) -> bool:
        """Determine if JOIN is needed based on prompt and documentation"""
        prompt_lower = prompt.lower()
        
        # Keywords that suggest JOINs
        join_keywords = ["with their", "and their", "including", "along with", "student application", "application document"]
        
        for keyword in join_keywords:
            if keyword in prompt_lower:
                return True
        
        # Check if multiple table names are mentioned
        if documentation and documentation.get("relationships"):
            table_names_in_prompt = []
            for rel in documentation["relationships"]:
                if rel["from_table"].lower() in prompt_lower:
                    table_names_in_prompt.append(rel["from_table"])
                if rel["to_table"].lower() in prompt_lower:
                    table_names_in_prompt.append(rel["to_table"])
            
            return len(set(table_names_in_prompt)) > 1
        
        return False

    def _find_join_tables_from_prompt(self, prompt: str, schema_info: Dict[str, Any]) -> List[str]:
        """Find tables that should be joined based on prompt content"""
        prompt_lower = prompt.lower()
        mentioned_tables = []
        
        if schema_info and "tables" in schema_info:
            for table_name in schema_info["tables"].keys():
                # Check both singular and plural forms
                table_variants = [
                    table_name.lower(),
                    table_name.lower()[:-1] if table_name.endswith('s') else table_name.lower() + 's'
                ]
                
                for variant in table_variants:
                    if variant in prompt_lower:
                        mentioned_tables.append(table_name)
                        break
        
        # Default combinations based on common patterns
        if len(mentioned_tables) < 2:
            if any(word in prompt_lower for word in ['student', 'students']):
                mentioned_tables = ['Students', 'Applications']
            elif any(word in prompt_lower for word in ['application', 'applications']):
                mentioned_tables = ['Applications', 'Documents']
        
        return list(set(mentioned_tables))  # Remove duplicates

    async def _schema_aware_sql_generation(self, prompt: str, schema_info: Optional[Dict[str, Any]] = None, connection_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Schema-aware SQL generation without LLM, with enum support"""
        prompt_lower = prompt.lower()
        
        # Get enum context if available
        enum_context = ""
        if connection_id:
            enum_context = await enum_service.get_enum_context(connection_id)
            
            # Check for enum-specific queries
            if "approved" in prompt_lower or "aprobada" in prompt_lower:
                # User is asking about approved status
                pass  # Will be handled by pattern matching below
            elif "pending" in prompt_lower or "evaluacion" in prompt_lower:
                # User is asking about pending/evaluation status
                pass  # Will be handled by pattern matching below
            elif "rejected" in prompt_lower or "rechazada" in prompt_lower:
                # User is asking about rejected status
                pass  # Will be handled by pattern matching below
        
        # If we have schema info, try to find relevant tables
        if schema_info and "tables" in schema_info and schema_info["tables"]:
            relevant_tables = self.schema_analyzer.find_relevant_tables(prompt, schema_info)
            
            # Enhanced patterns with MSSQL-specific syntax and schema awareness
            patterns = {
                r"show\s+tables?": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
                r"show\s+databases?": "SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name",  # Skip system DBs
                r"show\s+highschool|show\s+high\s+school": "SELECT TOP 100 * FROM HighSchools WITH (NOLOCK)",
                r"show\s+all\s+highschool|list\s+highschool": "SELECT * FROM HighSchools WITH (NOLOCK)",
                r"show\s+student": "SELECT TOP 100 * FROM Students WITH (NOLOCK)",
                r"show\s+application": "SELECT TOP 100 * FROM Applications WITH (NOLOCK)",
                r"describe\s+(\w+)": "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{}' ORDER BY ORDINAL_POSITION",
                r"student.*application|application.*student": lambda p, t, s: self._generate_join_query(p, t, s, connection_id),
                r"student.*document|document.*student": lambda p, t, s: self._generate_join_query(p, t, s, connection_id),
                r"application.*document|document.*application": lambda p, t, s: self._generate_join_query(p, t, s, connection_id),
                r"with\s+their|and\s+their|including": lambda p, t, s: self._generate_join_query(p, t, s, connection_id),
                r"approved|aprobada": lambda p, t, s: self._generate_enum_filter_query(p, t, s, "Status", "Aprobada", connection_id),
                r"rejected|rechazada": lambda p, t, s: self._generate_enum_filter_query(p, t, s, "Status", "Rechazada", connection_id),
                r"pending|evaluacion": lambda p, t, s: self._generate_enum_filter_query(p, t, s, "Status", "Evaluacion", connection_id),
                r"pagada|paid": lambda p, t, s: self._generate_enum_filter_query(p, t, s, "Status", "Pagada", connection_id),
                r"how\s+many": self._generate_count_query,
                r"count": self._generate_count_query,
                r"total": self._generate_count_query,
                r"number\s+of": self._generate_count_query,
                r"all": self._generate_select_all_query,
                r"list": self._generate_select_all_query,
                r"show\s+all": self._generate_select_all_query,
                r"average|avg": self._generate_avg_query,
                r"sum|total": self._generate_sum_query,
                r"max|maximum|highest": self._generate_max_query,
                r"min|minimum|lowest": self._generate_min_query,
            }
            
            for pattern, handler in patterns.items():
                if re.search(pattern, prompt_lower):
                    if callable(handler):
                        sql_query = handler(prompt_lower, relevant_tables, schema_info)
                    else:
                        sql_query = handler
                    
                    if sql_query:
                        result_type = self._determine_result_type(sql_query)
                        return sql_query, {"result_type": result_type}
        
        # Fall back to basic generation
        return self._basic_sql_generation(prompt)
    
    def _generate_count_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any]) -> str:
        """Generate COUNT query with MSSQL optimization"""
        if tables:
            return f"SELECT COUNT(*) AS total FROM {tables[0]} WITH (NOLOCK)"
        return ""
    
    def _generate_select_all_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any]) -> str:
        """Generate SELECT query with MSSQL-specific syntax"""
        if tables:
            # Use TOP for limiting results in MSSQL
            return f"SELECT TOP 100 * FROM {tables[0]} WITH (NOLOCK)"
        return ""
    
    def _generate_avg_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any]) -> str:
        """Generate AVG query with MSSQL optimization"""
        if not tables:
            return ""
        
        table = tables[0]
        # Look for numeric columns
        if table in schema_info.get("tables", {}):
            numeric_cols = [
                col["name"] for col in schema_info["tables"][table]["columns"]
                if col["data_type"] in ["int", "decimal", "float", "numeric", "money", "smallint", "bigint", "real", "tinyint"]
            ]
            if numeric_cols:
                # Try to find mentioned column
                for col in numeric_cols:
                    if col.lower() in prompt:
                        return f"SELECT AVG(CAST({col} AS FLOAT)) AS average_{col} FROM {table} WITH (NOLOCK)"
                # Default to first numeric column
                return f"SELECT AVG(CAST({numeric_cols[0]} AS FLOAT)) AS average FROM {table} WITH (NOLOCK)"
        return ""
    
    def _generate_sum_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any]) -> str:
        """Generate SUM query with MSSQL optimization"""
        if not tables:
            return ""
        
        table = tables[0]
        if table in schema_info.get("tables", {}):
            numeric_cols = [
                col["name"] for col in schema_info["tables"][table]["columns"]
                if col["data_type"] in ["int", "decimal", "float", "numeric", "money", "smallint", "bigint", "real", "tinyint"]
            ]
            if numeric_cols:
                for col in numeric_cols:
                    if col.lower() in prompt:
                        return f"SELECT SUM({col}) AS total_{col} FROM {table} WITH (NOLOCK)"
                return f"SELECT SUM({numeric_cols[0]}) AS total FROM {table} WITH (NOLOCK)"
        return ""
    
    def _generate_max_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any]) -> str:
        """Generate MAX query with MSSQL optimization"""
        if not tables:
            return ""
        
        table = tables[0]
        if table in schema_info.get("tables", {}):
            cols = schema_info["tables"][table]["columns"]
            for col in cols:
                if col["name"].lower() in prompt:
                    return f"SELECT MAX({col['name']}) AS max_{col['name']} FROM {table} WITH (NOLOCK)"
        return ""
    
    def _generate_min_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any]) -> str:
        """Generate MIN query with MSSQL optimization"""
        if not tables:
            return ""
        
        table = tables[0]
        if table in schema_info.get("tables", {}):
            cols = schema_info["tables"][table]["columns"]
            for col in cols:
                if col["name"].lower() in prompt:
                    return f"SELECT MIN({col['name']}) AS min_{col['name']} FROM {table} WITH (NOLOCK)"
        return ""
    
    def _generate_enum_filter_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any], 
                                   column_name: str, enum_value: str, connection_id: Optional[str]) -> str:
        """Generate query with enum filter, including JOINs when necessary"""
        if not tables:
            return ""
        
        # Detect if we need to join tables
        join_query = self._detect_and_build_join(prompt, tables, schema_info, column_name, enum_value, connection_id)
        if join_query:
            return join_query
        
        table = tables[0]
        
        # Get the numeric value for the enum
        numeric_value = None
        if connection_id:
            suggestions = enum_service.get_enum_suggestions(connection_id)
            
            # Check different enum types for the value
            for enum_type, values in suggestions.items():
                for value_info in values:
                    if value_info["label"] == enum_value:
                        numeric_value = value_info["value"]
                        break
                if numeric_value is not None:
                    break
        
        # If we found the numeric value, use it
        if numeric_value is not None:
            # Check if it's a count query
            if "count" in prompt.lower() or "how many" in prompt.lower():
                return f"SELECT COUNT(*) AS total FROM {table} WHERE {column_name} = {numeric_value}"
            else:
                return f"SELECT * FROM {table} WHERE {column_name} = {numeric_value}"
        
        # Fallback to basic query
        return f"SELECT * FROM {table}"
    
    def _detect_and_build_join(self, prompt: str, tables: List[str], schema_info: Dict[str, Any], 
                               column_name: str, enum_value: str, connection_id: Optional[str]) -> Optional[str]:
        """Detect if JOIN is needed and build the query"""
        prompt_lower = prompt.lower()
        
        # Keywords that suggest we need information from multiple tables
        join_indicators = [
            ("student", "application"),
            ("student", "document"),
            ("student", "scholarship"),
            ("application", "document"),
            ("application", "scholarship"),
            ("application", "review"),
            ("student", "receipt"),
            ("with their", "and their"),
            ("including", "along with"),
            ("join", "joined"),
        ]
        
        # Check if prompt suggests joining tables
        needs_join = False
        for indicator1, indicator2 in join_indicators:
            if indicator1 in prompt_lower and indicator2 in prompt_lower:
                needs_join = True
                break
        
        # Also check if multiple table names are mentioned
        mentioned_tables = []
        if schema_info and "tables" in schema_info:
            for table_name in schema_info["tables"].keys():
                if table_name.lower() in prompt_lower or table_name[:-1].lower() in prompt_lower:
                    mentioned_tables.append(table_name)
        
        if len(mentioned_tables) > 1:
            needs_join = True
        
        if not needs_join and len(tables) <= 1:
            return None
        
        # Build JOIN query based on common patterns
        if needs_join or len(tables) > 1:
            return self._build_join_query(prompt, tables if tables else mentioned_tables, 
                                         schema_info, column_name, enum_value, connection_id)
        
        return None
    
    def _build_join_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any],
                         column_name: str, enum_value: str, connection_id: Optional[str]) -> str:
        """Build a JOIN query based on table relationships"""
        prompt_lower = prompt.lower()
        
        # Get numeric value for enum if provided
        numeric_value = None
        if connection_id and enum_value:
            suggestions = enum_service.get_enum_suggestions(connection_id)
            for enum_type, values in suggestions.items():
                for value_info in values:
                    if value_info["label"] == enum_value:
                        numeric_value = value_info["value"]
                        break
                if numeric_value is not None:
                    break
        
        # Common JOIN patterns for scholarship system with MSSQL optimization
        join_patterns = {
            ("students", "applications"): {
                "query": "SELECT s.*, a.* FROM Students s WITH (NOLOCK) INNER JOIN Applications a WITH (NOLOCK) ON s.Id = a.StudentId",
                "filter_table": "a"
            },
            ("students", "documents"): {
                "query": "SELECT s.*, d.* FROM Students s WITH (NOLOCK) INNER JOIN Applications a WITH (NOLOCK) ON s.Id = a.StudentId INNER JOIN Documents d WITH (NOLOCK) ON a.Id = d.ApplicationId",
                "filter_table": "d"
            },
            ("applications", "documents"): {
                "query": "SELECT a.*, d.* FROM Applications a WITH (NOLOCK) INNER JOIN Documents d WITH (NOLOCK) ON a.Id = d.ApplicationId",
                "filter_table": "a"
            },
            ("applications", "scholarships"): {
                "query": "SELECT a.*, sch.* FROM Applications a WITH (NOLOCK) INNER JOIN Scholarships sch WITH (NOLOCK) ON a.Id = sch.ApplicationId",
                "filter_table": "a"
            },
            ("students", "scholarships"): {
                "query": "SELECT s.*, a.*, sch.* FROM Students s WITH (NOLOCK) INNER JOIN Applications a WITH (NOLOCK) ON s.Id = a.StudentId INNER JOIN Scholarships sch WITH (NOLOCK) ON a.Id = sch.ApplicationId",
                "filter_table": "a"
            },
            ("applications", "reviews"): {
                "query": "SELECT a.*, r.* FROM Applications a WITH (NOLOCK) INNER JOIN ApplicationReviews r WITH (NOLOCK) ON a.Id = r.ApplicationId",
                "filter_table": "a"
            },
        }
        
        # Try to find matching pattern
        base_query = None
        filter_table_alias = "a"  # default
        
        for (table1, table2), pattern_info in join_patterns.items():
            if any(t1 in prompt_lower for t1 in [table1, table1[:-1]]) and \
               any(t2 in prompt_lower for t2 in [table2, table2[:-1]]):
                base_query = pattern_info["query"]
                filter_table_alias = pattern_info["filter_table"]
                break
        
        # If no pattern matched but we have tables, create a simple join
        if not base_query and len(tables) >= 2:
            # Assume first table has Id and second has FirstTableId
            table1 = tables[0]
            table2 = tables[1]
            base_query = f"SELECT t1.*, t2.* FROM {table1} t1 INNER JOIN {table2} t2 ON t1.Id = t2.{table1[:-1]}Id"
            filter_table_alias = "t1"
        
        if not base_query:
            # Fallback to first table
            if tables:
                base_query = f"SELECT * FROM {tables[0]}"
                filter_table_alias = ""
        
        # Add WHERE clause if we have enum filter
        if numeric_value is not None and base_query:
            if filter_table_alias:
                where_column = f"{filter_table_alias}.{column_name}"
            else:
                where_column = column_name
            
            if "count" in prompt_lower or "how many" in prompt_lower:
                # Modify for COUNT query
                base_query = base_query.replace("SELECT s.*, a.*", "SELECT COUNT(*)")
                base_query = base_query.replace("SELECT a.*, d.*", "SELECT COUNT(*)")
                base_query = base_query.replace("SELECT s.*, a.*, sch.*", "SELECT COUNT(*)")
                base_query = base_query.replace("SELECT t1.*, t2.*", "SELECT COUNT(*)")
                base_query = base_query.replace("SELECT *", "SELECT COUNT(*)")
                base_query += f" WHERE {where_column} = {numeric_value}"
            else:
                base_query += f" WHERE {where_column} = {numeric_value}"
        
        return base_query
    
    def _generate_join_query(self, prompt: str, tables: List[str], schema_info: Dict[str, Any], 
                            connection_id: Optional[str]) -> str:
        """Generate JOIN query without enum filter"""
        prompt_lower = prompt.lower()
        
        # Check for enum values in the prompt
        enum_value = None
        column_name = "Status"  # default
        
        if "approved" in prompt_lower or "aprobada" in prompt_lower:
            enum_value = "Aprobada"
        elif "rejected" in prompt_lower or "rechazada" in prompt_lower:
            enum_value = "Rechazada"
        elif "pending" in prompt_lower or "evaluacion" in prompt_lower:
            enum_value = "Evaluacion"
        elif "pagada" in prompt_lower or "paid" in prompt_lower:
            enum_value = "Pagada"
        
        # Use the existing join builder
        return self._build_join_query(prompt, tables, schema_info, column_name, enum_value, connection_id)
    
    def _basic_sql_generation(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Basic SQL generation without LLM using MSSQL syntax"""
        prompt_lower = prompt.lower()
        
        # MSSQL-specific pattern matching
        patterns = {
            r"show\s+tables?": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
            r"show\s+databases?": "SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name",
            r"show\s+highschool|show\s+high\s+school": "SELECT TOP 100 * FROM HighSchools WITH (NOLOCK)",
            r"list\s+highschool|all\s+highschool": "SELECT * FROM HighSchools WITH (NOLOCK)",
            r"show\s+student": "SELECT TOP 100 * FROM Students WITH (NOLOCK)",
            r"show\s+application": "SELECT TOP 100 * FROM Applications WITH (NOLOCK)",
            r"show\s+scholarship": "SELECT TOP 100 * FROM Scholarships WITH (NOLOCK)",
            r"describe\s+(\w+)": "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{}' ORDER BY ORDINAL_POSITION",
            r"count\s+.*\s+from\s+(\w+)": "SELECT COUNT(*) AS total FROM {} WITH (NOLOCK)",
            r"how\s+many\s+(\w+)": "SELECT COUNT(*) AS total FROM {} WITH (NOLOCK)",
            r"count\s+(\w+)": "SELECT COUNT(*) AS total FROM {} WITH (NOLOCK)",
            r"total\s+(\w+)": "SELECT COUNT(*) AS total FROM {} WITH (NOLOCK)",
            r"number\s+of\s+(\w+)": "SELECT COUNT(*) AS total FROM {} WITH (NOLOCK)",
            r"select\s+.*\s+from\s+(\w+)": prompt.upper() if prompt_lower.startswith("select") else "SELECT TOP 100 * FROM {} WITH (NOLOCK)"
        }
        
        for pattern, template in patterns.items():
            match = re.search(pattern, prompt_lower)
            if match:
                if "{}" in template and match.groups():
                    sql_query = template.format(match.group(1))
                else:
                    sql_query = template
                
                result_type = self._determine_result_type(sql_query)
                return sql_query, {"result_type": result_type}
        
        # If no pattern matches, return the prompt as-is (assuming it might be SQL)
        if any(keyword in prompt_lower for keyword in ['select', 'insert', 'update', 'delete', 'create', 'drop']):
            return prompt, {"result_type": self._determine_result_type(prompt)}
        
        return "", {"error": "Could not generate SQL from prompt", "result_type": "error"}
    
    def _determine_result_type(self, sql_query: str) -> str:
        """Determine if the result should be displayed as text or table"""
        sql_lower = sql_query.lower()
        
        # Queries that typically return tables
        table_indicators = [
            'select * from',
            'select top',
            'group by',
            'order by',
            'join',
            'where',
            'having'
        ]
        
        # Queries that typically return single values or messages
        text_indicators = [
            'count(*)',
            'sum(',
            'avg(',
            'max(',
            'min(',
            'select 1',
            'select @@'
        ]
        
        # Check for text indicators first (more specific)
        for indicator in text_indicators:
            if indicator in sql_lower:
                return "text"
        
        # Check for table indicators
        for indicator in table_indicators:
            if indicator in sql_lower:
                return "table"
        
        # Default based on query type
        if sql_lower.startswith('select'):
            return "table"
        else:
            return "text"