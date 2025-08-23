from typing import Dict, List, Any, Optional
import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SchemaAnalyzer:
    def __init__(self):
        self.schema_cache: Dict[str, Any] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
        self.redis_service = None
    
    def set_redis_service(self, redis_service):
        """Set Redis service for caching"""
        self.redis_service = redis_service
    
    async def get_database_schema(self, engine: Engine, connection_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get complete database schema with tables, columns, and relationships"""
        
        # Check Redis cache first if available
        if not force_refresh and self.redis_service and self.redis_service.is_connected:
            cached_schema = await self.redis_service.get_cached_schema(connection_id)
            if cached_schema:
                logger.info(f"Schema loaded from Redis cache for connection {connection_id}")
                return cached_schema
        
        # Check in-memory cache as fallback
        if not force_refresh and connection_id in self.schema_cache:
            if datetime.now() < self.cache_expiry.get(connection_id, datetime.min):
                logger.info(f"Schema loaded from memory cache for connection {connection_id}")
                return self.schema_cache[connection_id]
        
        schema_info = {
            "tables": {},
            "relationships": [],
            "statistics": {},
            "analyzed_at": datetime.now().isoformat()
        }
        
        try:
            # Get all tables
            with engine.connect() as conn:
                # Get table names
                tables_query = text("""
                    SELECT TABLE_NAME, TABLE_TYPE 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW')
                    AND TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'sys', 'master', 'tempdb', 'model', 'msdb')
                """)
                
                tables_result = conn.execute(tables_query)
                tables = tables_result.fetchall()
                
                for table_name, table_type in tables:
                    schema_info["tables"][table_name] = {
                        "type": table_type,
                        "columns": [],
                        "primary_keys": [],
                        "foreign_keys": [],
                        "indexes": [],
                        "row_count": 0,
                        "sample_data": []
                    }
                    
                    # Get columns for each table
                    columns_query = text("""
                        SELECT 
                            COLUMN_NAME,
                            DATA_TYPE,
                            IS_NULLABLE,
                            CHARACTER_MAXIMUM_LENGTH,
                            NUMERIC_PRECISION,
                            NUMERIC_SCALE,
                            COLUMN_DEFAULT
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = :table_name
                        ORDER BY ORDINAL_POSITION
                    """)
                    
                    columns_result = conn.execute(columns_query, {"table_name": table_name})
                    columns = columns_result.fetchall()
                    
                    for col in columns:
                        column_info = {
                            "name": col[0],
                            "data_type": col[1],
                            "nullable": col[2] == "YES",
                            "max_length": col[3],
                            "precision": col[4],
                            "scale": col[5],
                            "default": col[6]
                        }
                        schema_info["tables"][table_name]["columns"].append(column_info)
                    
                    # Get primary keys
                    pk_query = text("""
                        SELECT COLUMN_NAME
                        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                        WHERE TABLE_NAME = :table_name
                        AND CONSTRAINT_NAME LIKE 'PK_%'
                    """)
                    
                    pk_result = conn.execute(pk_query, {"table_name": table_name})
                    primary_keys = [row[0] for row in pk_result.fetchall()]
                    schema_info["tables"][table_name]["primary_keys"] = primary_keys
                    
                    # Get foreign keys
                    fk_query = text("""
                        SELECT 
                            fk.COLUMN_NAME,
                            pk.TABLE_NAME as REFERENCED_TABLE,
                            pk.COLUMN_NAME as REFERENCED_COLUMN
                        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE fk
                            ON rc.CONSTRAINT_NAME = fk.CONSTRAINT_NAME
                        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
                            ON rc.UNIQUE_CONSTRAINT_NAME = pk.CONSTRAINT_NAME
                        WHERE fk.TABLE_NAME = :table_name
                    """)
                    
                    try:
                        fk_result = conn.execute(fk_query, {"table_name": table_name})
                        foreign_keys = []
                        for fk in fk_result.fetchall():
                            fk_info = {
                                "column": fk[0],
                                "referenced_table": fk[1],
                                "referenced_column": fk[2]
                            }
                            foreign_keys.append(fk_info)
                            
                            # Add to relationships
                            schema_info["relationships"].append({
                                "from_table": table_name,
                                "from_column": fk[0],
                                "to_table": fk[1],
                                "to_column": fk[2],
                                "type": "foreign_key"
                            })
                        
                        schema_info["tables"][table_name]["foreign_keys"] = foreign_keys
                    except:
                        pass  # Some databases don't support foreign keys well
                    
                    # Get approximate row count
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                        count_result = conn.execute(count_query)
                        row_count = count_result.scalar()
                        schema_info["tables"][table_name]["row_count"] = row_count
                    except:
                        pass
                    
                    # Get sample data (first 3 rows)
                    try:
                        sample_query = text(f"SELECT TOP 3 * FROM {table_name}")
                        sample_result = conn.execute(sample_query)
                        sample_data = []
                        for row in sample_result.fetchall():
                            row_dict = {}
                            for key, value in row._mapping.items():
                                # Convert non-JSON serializable types to strings
                                if hasattr(value, 'isoformat'):  # datetime, date, time objects
                                    row_dict[key] = value.isoformat()
                                elif value.__class__.__name__ in ['Decimal', 'UUID', 'Timestamp']:
                                    row_dict[key] = str(value)
                                else:
                                    row_dict[key] = value
                            sample_data.append(row_dict)
                        schema_info["tables"][table_name]["sample_data"] = sample_data
                    except:
                        pass
                
                # Calculate statistics
                schema_info["statistics"] = {
                    "total_tables": len(schema_info["tables"]),
                    "total_columns": sum(len(t["columns"]) for t in schema_info["tables"].values()),
                    "total_relationships": len(schema_info["relationships"]),
                    "total_rows": sum(t.get("row_count", 0) for t in schema_info["tables"].values())
                }
            
            # Cache the schema
            # Store in memory cache
            self.schema_cache[connection_id] = schema_info
            self.cache_expiry[connection_id] = datetime.now() + self.cache_duration
            
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
            
        except Exception as e:
            return {
                "error": str(e),
                "tables": {},
                "relationships": [],
                "statistics": {}
            }
    
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
        
        if schema_info["relationships"]:
            context_parts.append("\nRelationships:")
            for rel in schema_info["relationships"]:
                context_parts.append(f"  {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
        
        return "\n".join(context_parts)
    
    def find_relevant_tables(self, query: str, schema_info: Dict[str, Any]) -> List[str]:
        """Find tables that might be relevant to the query"""
        
        if not schema_info or "error" in schema_info:
            return []
        
        query_lower = query.lower()
        relevant_tables = []
        
        for table_name, table_info in schema_info["tables"].items():
            table_name_lower = table_name.lower()
            
            # Check if table name is mentioned
            if table_name_lower in query_lower:
                relevant_tables.append(table_name)
                continue
            
            # Check for singular/plural forms
            if table_name_lower.endswith('s'):
                singular = table_name_lower[:-1]
                if singular in query_lower:
                    relevant_tables.append(table_name)
                    continue
            else:
                plural = table_name_lower + 's'
                if plural in query_lower:
                    relevant_tables.append(table_name)
                    continue
            
            # Check if any column names are mentioned
            for col in table_info["columns"]:
                if col["name"].lower() in query_lower:
                    relevant_tables.append(table_name)
                    break
        
        return list(set(relevant_tables))  # Remove duplicates