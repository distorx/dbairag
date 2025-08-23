from typing import Dict, List, Any, Optional
import asyncio
from sqlalchemy import text, inspect, create_engine
from sqlalchemy.engine import Engine
import json
from datetime import datetime, timedelta
import logging
from ..services import MSSQLService
from .field_analyzer_service import FieldAnalyzerService

logger = logging.getLogger(__name__)

class SchemaAnalyzer:
    def __init__(self):
        from .dynamic_fuzzy_matcher import DynamicFuzzyMatcher
        self.schema_cache: Dict[str, Any] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        self.redis_service = None
        self.field_analyzer = FieldAnalyzerService()
        self.fuzzy_matcher = DynamicFuzzyMatcher()
    
    def set_redis_service(self, redis_service):
        """Set Redis service for caching"""
        self.redis_service = redis_service
    
    def create_engine(self, connection_string: str) -> Engine:
        """Create SQLAlchemy engine from connection string"""
        # Check if it's already a SQLAlchemy URL format
        if connection_string.startswith(('sqlite://', 'postgresql://', 'mysql://', 'mssql://')):
            # It's already in SQLAlchemy format, use it directly
            return create_engine(connection_string)
        
        # Otherwise, parse it as MSSQL connection string
        params = MSSQLService.parse_connection_string(connection_string)
        server = params.get('server', 'localhost')
        database = params.get('database', 'master')
        username = params.get('user id') or params.get('uid')
        password = params.get('password') or params.get('pwd')
        
        # Create SQLAlchemy engine URL for MSSQL
        engine_url = f"mssql+pymssql://{username}:{password}@{server}/{database}"
        return create_engine(engine_url)
    
    async def get_database_schema(self, engine: Engine, connection_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get complete database schema with tables, columns, and relationships"""
        
        # Check Redis cache first if available
        if not force_refresh and self.redis_service and self.redis_service.is_connected:
            cached_schema = await self.redis_service.get_cached_schema(connection_id)
            if cached_schema:
                logger.info(f"Schema loaded from Redis cache for connection {connection_id}")
                # Ensure fuzzy matcher learns from cached schema
                if cached_schema and "tables" in cached_schema:
                    self.fuzzy_matcher.learn_from_schema(cached_schema)
                return cached_schema
        
        # Check in-memory cache as fallback
        if not force_refresh and connection_id in self.schema_cache:
            if datetime.now() < self.cache_expiry.get(connection_id, datetime.min):
                logger.info(f"Schema loaded from memory cache for connection {connection_id}")
                cached_schema = self.schema_cache[connection_id]
                # Ensure fuzzy matcher learns from cached schema
                if cached_schema and "tables" in cached_schema:
                    self.fuzzy_matcher.learn_from_schema(cached_schema)
                return cached_schema
        
        # Use the universal schema analyzer for all database types
        from .schema_analyzer_universal import UniversalSchemaAnalyzer
        universal_analyzer = UniversalSchemaAnalyzer()
        schema_info = await universal_analyzer.get_database_schema(engine, connection_id, force_refresh)
        
        # Ensure the schema was analyzed successfully
        if not schema_info or "error" in schema_info:
            logger.error(f"Failed to analyze schema: {schema_info.get('error', 'Unknown error')}")
            return schema_info or {
                "tables": {},
                "relationships": [],
                "statistics": {"error": "Failed to analyze schema"},
                "analyzed_at": datetime.now().isoformat()
            }
        
        # Teach fuzzy matcher from schema
        if schema_info and "tables" in schema_info:
            self.fuzzy_matcher.learn_from_schema(schema_info)
            logger.info(f"Fuzzy matcher learned from {len(schema_info['tables'])} tables")
        
        # Cache the schema
        # Store in memory cache
        self.schema_cache[connection_id] = schema_info
        self.cache_expiry[connection_id] = datetime.now() + self.cache_duration
        
        # Add field analysis for semantic insights
        try:
            field_analysis = self.field_analyzer.analyze_database_fields(schema_info)
            schema_info["field_analysis"] = field_analysis
            logger.info(f"Field analysis completed for connection {connection_id}")
        except Exception as e:
            logger.error(f"Field analysis failed for connection {connection_id}: {e}")
            schema_info["field_analysis"] = {"error": str(e)}
        
        # Store in Redis cache if available
        if self.redis_service and self.redis_service.is_connected:
            from ..config import settings
            await self.redis_service.cache_schema(
                connection_id, 
                schema_info,
                ttl=settings.cache_ttl_schema
            )
            logger.info(f"Schema cached in Redis for connection {connection_id}")
        
        return schema_info
    
    def _collect_enhanced_samples(self, conn, table_name, columns):
        """Collect intelligent sample data for better LLM understanding"""
        
        # Find primary key column for ordering
        primary_key = None
        created_at_col = None
        updated_at_col = None
        
        for col in columns:
            col_name = col["name"].lower()
            if col_name.endswith("_id") or col_name == "id":
                primary_key = col["name"]
            elif col_name in ["created_at", "createdate", "creation_date"]:
                created_at_col = col["name"]
            elif col_name in ["updated_at", "updatedate", "modification_date"]:
                updated_at_col = col["name"]
        
        sample_strategies = []
        
        # Strategy 1: Recent data (if timestamp columns exist)
        if created_at_col:
            sample_strategies.append(f"SELECT TOP 2 * FROM [{table_name}] ORDER BY [{created_at_col}] DESC")
        
        if updated_at_col and updated_at_col != created_at_col:
            sample_strategies.append(f"SELECT TOP 2 * FROM [{table_name}] ORDER BY [{updated_at_col}] DESC")
        
        # Strategy 2: Diverse samples using primary key
        if primary_key:
            sample_strategies.append(f"SELECT TOP 3 * FROM [{table_name}] WHERE [{primary_key}] IS NOT NULL ORDER BY [{primary_key}]")
        
        # Strategy 3: Random sampling (SQL Server compatible)
        sample_strategies.append(f"SELECT TOP 3 * FROM [{table_name}] ORDER BY NEWID()")
        
        # Strategy 4: Basic fallback
        sample_strategies.append(f"SELECT TOP 5 * FROM [{table_name}]")
        
        all_samples = []
        unique_samples = []
        seen_keys = set()
        
        for strategy in sample_strategies:
            try:
                result = conn.execute(text(strategy))
                rows = result.fetchall()
                
                for row in rows:
                    row_dict = {}
                    for key, value in row._mapping.items():
                        # Convert non-JSON serializable types to strings
                        if hasattr(value, 'isoformat'):  # datetime, date, time objects
                            row_dict[key] = value.isoformat()
                        elif value.__class__.__name__ in ['Decimal', 'UUID', 'Timestamp']:
                            row_dict[key] = str(value)
                        elif value is None:
                            row_dict[key] = None
                        else:
                            row_dict[key] = value
                    all_samples.append(row_dict)
                    
            except Exception as e:
                logger.debug(f"Sample strategy failed for {table_name}: {strategy} - {str(e)}")
                continue
        
        # Remove duplicates based on primary key or first column
        key_column = primary_key or (columns[0]["name"] if columns else "id")
        
        for sample in all_samples:
            key_value = str(sample.get(key_column, ""))
            if key_value and key_value not in seen_keys:
                unique_samples.append(sample)
                seen_keys.add(key_value)
                
                # Limit to 8 diverse samples per table
                if len(unique_samples) >= 8:
                    break
        
        return unique_samples
    
    def get_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Generate a text description of the schema for LLM context"""
        
        if not schema_info or "error" in schema_info:
            return "No schema information available."
        
        context_parts = []
        context_parts.append("Database Schema Information:")
        context_parts.append(f"Total Tables: {schema_info['statistics'].get('total_tables', 0)}")
        context_parts.append(f"Total Rows: {schema_info['statistics'].get('total_rows', 0)}")
        context_parts.append("\nTables:")
        
        for table_name, table_info in schema_info["tables"].items():
            context_parts.append(f"\n{table_name} ({table_info.get('row_count', 0)} rows):")
            context_parts.append("  Columns:")
            
            for col in table_info["columns"]:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                context_parts.append(f"    - {col['name']} ({col['data_type']}) {nullable}")
            
            if table_info["primary_keys"]:
                context_parts.append(f"  Primary Keys: {', '.join(table_info['primary_keys'])}")
            
            if table_info["foreign_keys"]:
                context_parts.append("  Foreign Keys:")
                for fk in table_info["foreign_keys"]:
                    context_parts.append(f"    - {fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}")
            
            # Add sample data context for better LLM understanding
            if table_info.get("sample_data"):
                context_parts.append("  Sample Data Examples:")
                for i, sample in enumerate(table_info["sample_data"][:2]):  # Show 2 samples
                    context_parts.append(f"    Example {i+1}: {dict(list(sample.items())[:3])}...")  # Show first 3 fields
                
                # Add insights about data patterns
                self._add_data_insights(context_parts, table_name, table_info["sample_data"])
        
        if schema_info["relationships"]:
            context_parts.append("\nRelationships:")
            for rel in schema_info["relationships"]:
                context_parts.append(f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
        
        return "\n".join(context_parts)
    
    def find_relevant_tables(self, query: str, schema_info: Dict[str, Any]) -> List[str]:
        """Find tables that might be relevant to the query, using fuzzy matching"""
        
        logger.info(f"find_relevant_tables called with query: '{query}'")
        
        if not schema_info or "error" in schema_info:
            logger.warning("No valid schema_info provided")
            return []
        
        logger.info(f"Schema has {len(schema_info.get('tables', {}))} tables")
        
        # Teach fuzzy matcher from schema if not already done
        if schema_info and "tables" in schema_info:
            self.fuzzy_matcher.learn_from_schema(schema_info)
        
        query_lower = query.lower()
        relevant_tables = []
        words = query_lower.split()
        
        # Look for potential table references in the query
        for word in words:
            # Skip SQL keywords
            if word in ['select', 'from', 'where', 'count', 'sum', 'avg', 'join', 'insert', 'update', 'delete']:
                continue
            
            # ALWAYS use fuzzy matching - it will prefer tables with data over empty ones
            match_result = self.fuzzy_matcher.find_best_table_match(word)
            if match_result:
                matched_table, confidence = match_result
                if confidence >= 60:  # Lower threshold since fuzzy matcher prefers tables with data
                    relevant_tables.append(matched_table)
                    logger.info(f"Fuzzy matched '{word}' to table '{matched_table}' (confidence: {confidence})")
                    continue
            
            # Fallback to exact matching
            for table_name, table_info in schema_info["tables"].items():
                table_name_lower = table_name.lower()
                
                # Check if table name is mentioned
                if table_name_lower in query_lower:
                    relevant_tables.append(table_name)
                    break
                
                # Check for singular/plural forms
                if table_name_lower.endswith('s'):
                    singular = table_name_lower[:-1]
                    if singular in query_lower:
                        relevant_tables.append(table_name)
                        break
                else:
                    plural = table_name_lower + 's'
                    if plural in query_lower:
                        relevant_tables.append(table_name)
                        break
                
                # Check if any column names are mentioned
                for col in table_info["columns"]:
                    if col["name"].lower() in query_lower:
                        relevant_tables.append(table_name)
                        break
        
        return list(set(relevant_tables))  # Remove duplicates
    
    def _add_data_insights(self, context_parts, table_name, sample_data):
        """Add insights about data patterns from sample data"""
        
        if not sample_data:
            return
        
        insights = []
        
        # Analyze first few samples for patterns
        first_sample = sample_data[0] if sample_data else {}
        
        for column, value in first_sample.items():
            if value is None:
                continue
                
            # Email pattern detection
            if isinstance(value, str) and '@' in value and '.' in value:
                insights.append(f"{column} contains email addresses")
            
            # Status/enum pattern detection
            elif isinstance(value, str) and len(value) < 20:
                # Check if it's a common status value
                status_keywords = ['active', 'inactive', 'pending', 'completed', 'draft', 'published']
                if any(keyword in value.lower() for keyword in status_keywords):
                    insights.append(f"{column} appears to be a status field")
            
            # ID pattern detection
            elif isinstance(value, (int, str)) and str(column).lower().endswith('_id'):
                insights.append(f"{column} is a reference ID field")
            
            # Date pattern detection
            elif isinstance(value, str) and any(char in value for char in ['-', '/', 'T']):
                try:
                    from datetime import datetime
                    # Try to parse as date
                    if len(value) > 8:  # Reasonable date string length
                        insights.append(f"{column} contains date/time values")
                except:
                    pass
        
        # Add table-level insights
        if table_name.lower() in ['users', 'customers', 'students', 'employees']:
            insights.append(f"This appears to be a {table_name.lower()} master table")
        elif table_name.lower() in ['orders', 'transactions', 'payments', 'enrollments']:
            insights.append(f"This appears to be a transactional {table_name.lower()} table")
        elif '_log' in table_name.lower() or 'history' in table_name.lower():
            insights.append("This appears to be an audit/log table")
        
        if insights:
            context_parts.append("  Data Insights:")
            for insight in insights[:3]:  # Limit to top 3 insights
                context_parts.append(f"    * {insight}")