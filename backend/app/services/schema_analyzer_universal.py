"""
Universal schema analyzer that works with all database types using SQLAlchemy Inspector
"""
from typing import Dict, List, Any, Optional
import asyncio
from sqlalchemy import text, inspect, create_engine
from sqlalchemy.engine import Engine
import json
from datetime import datetime, timedelta
import logging
from .field_analyzer_service import FieldAnalyzerService

logger = logging.getLogger(__name__)

class UniversalSchemaAnalyzer:
    def __init__(self):
        self.schema_cache: Dict[str, Any] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(hours=1)
        self.redis_service = None
        self.field_analyzer = FieldAnalyzerService()
    
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
        from ..services import MSSQLService
        params = MSSQLService.parse_connection_string(connection_string)
        server = params.get('server', 'localhost')
        database = params.get('database', 'master')
        username = params.get('user id') or params.get('uid')
        password = params.get('password') or params.get('pwd')
        
        # Create SQLAlchemy engine URL for MSSQL
        engine_url = f"mssql+pymssql://{username}:{password}@{server}/{database}"
        return create_engine(engine_url)
    
    async def get_database_schema(self, engine: Engine, connection_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get complete database schema using SQLAlchemy Inspector - works with all databases"""
        
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
        
        # Analyze schema using SQLAlchemy Inspector (universal approach)
        schema_info = {
            "tables": {},
            "relationships": [],
            "statistics": {},
            "analyzed_at": datetime.now().isoformat()
        }
        
        try:
            # Use SQLAlchemy Inspector for universal database support
            inspector = inspect(engine)
            
            # Get all table names
            table_names = inspector.get_table_names()
            view_names = inspector.get_view_names()
            all_tables = table_names + view_names
            
            for table_name in all_tables:
                table_type = "VIEW" if table_name in view_names else "TABLE"
                
                schema_info["tables"][table_name] = {
                    "type": table_type,
                    "columns": [],
                    "primary_keys": [],
                    "foreign_keys": [],
                    "indexes": [],
                    "row_count": 0,
                    "sample_data": []
                }
                
                # Get columns
                columns = inspector.get_columns(table_name)
                for col in columns:
                    column_info = {
                        "name": col["name"],
                        "data_type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "default": str(col.get("default", "")) if col.get("default") else None,
                        "autoincrement": col.get("autoincrement", False),
                        "primary_key": False  # Will be updated below
                    }
                    schema_info["tables"][table_name]["columns"].append(column_info)
                
                # Get primary keys
                pk_constraint = inspector.get_pk_constraint(table_name)
                if pk_constraint and pk_constraint.get("constrained_columns"):
                    primary_keys = pk_constraint["constrained_columns"]
                    schema_info["tables"][table_name]["primary_keys"] = primary_keys
                    
                    # Mark primary key columns
                    for col in schema_info["tables"][table_name]["columns"]:
                        if col["name"] in primary_keys:
                            col["primary_key"] = True
                
                # Get foreign keys
                foreign_keys = inspector.get_foreign_keys(table_name)
                for fk in foreign_keys:
                    fk_info = {
                        "column": fk["constrained_columns"][0] if fk["constrained_columns"] else None,
                        "referenced_table": fk["referred_table"],
                        "referenced_column": fk["referred_columns"][0] if fk["referred_columns"] else None
                    }
                    schema_info["tables"][table_name]["foreign_keys"].append(fk_info)
                    
                    # Add to relationships
                    if fk_info["column"] and fk_info["referenced_table"]:
                        schema_info["relationships"].append({
                            "from_table": table_name,
                            "from_column": fk_info["column"],
                            "to_table": fk_info["referenced_table"],
                            "to_column": fk_info["referenced_column"],
                            "type": "foreign_key",
                            "confidence": 1.0
                        })
                
                # Get indexes
                indexes = inspector.get_indexes(table_name)
                schema_info["tables"][table_name]["indexes"] = [
                    {
                        "name": idx.get("name"),
                        "columns": idx.get("column_names", []),
                        "unique": idx.get("unique", False)
                    }
                    for idx in indexes
                ]
                
                # Get row count and sample data
                try:
                    with engine.connect() as conn:
                        # Get row count
                        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                        count_result = conn.execute(count_query)
                        row_count = count_result.scalar()
                        schema_info["tables"][table_name]["row_count"] = row_count or 0
                        
                        # Mark if table is empty
                        schema_info["tables"][table_name]["is_empty"] = (row_count == 0 or row_count is None)
                        
                        # Get sample data (limit to 5 rows)
                        if row_count and row_count > 0:
                            # Use appropriate syntax for LIMIT based on database type
                            if str(engine.url).startswith('mssql'):
                                sample_query = text(f"SELECT TOP 5 * FROM {table_name}")
                            else:
                                sample_query = text(f"SELECT * FROM {table_name} LIMIT 5")
                            sample_result = conn.execute(sample_query)
                            samples = []
                            for row in sample_result:
                                # Convert row to dict
                                sample = dict(row._mapping) if hasattr(row, '_mapping') else dict(zip(sample_result.keys(), row))
                                samples.append(sample)
                            schema_info["tables"][table_name]["sample_data"] = samples
                        else:
                            # Table is empty - mark it clearly
                            schema_info["tables"][table_name]["sample_data"] = []
                            logger.info(f"Table '{table_name}' is EMPTY (0 rows)")
                except Exception as e:
                    logger.warning(f"Failed to collect sample data for {table_name}: {str(e)}")
                    schema_info["tables"][table_name]["sample_data"] = []
            
            # Infer additional relationships based on naming patterns
            inferred_relationships = self._infer_relationships(schema_info["tables"])
            schema_info["relationships"].extend(inferred_relationships)
            
            # Calculate statistics
            schema_info["statistics"] = {
                "total_tables": len(table_names),
                "total_views": len(view_names),
                "total_columns": sum(len(t["columns"]) for t in schema_info["tables"].values()),
                "total_relationships": len(schema_info["relationships"]),
                "total_rows": sum(t.get("row_count", 0) for t in schema_info["tables"].values())
            }
            
            # Perform field analysis with dynamic fuzzy matching
            try:
                # Learn from schema for fuzzy matching
                from .dynamic_fuzzy_matcher import DynamicFuzzyMatcher
                fuzzy_matcher = DynamicFuzzyMatcher()
                fuzzy_matcher.learn_from_schema(schema_info)
                
                # Store fuzzy matcher patterns in schema info
                schema_info["fuzzy_patterns"] = {
                    "learned_mappings": dict(fuzzy_matcher.learned_mappings),
                    "compound_tables": fuzzy_matcher.compound_tables,
                    "table_patterns": dict(fuzzy_matcher.table_patterns)
                }
                
                # Also run field analysis
                field_analysis = self.field_analyzer.analyze_database_fields(
                    schema_info
                )
                schema_info["field_analysis"] = field_analysis
                
            except Exception as e:
                logger.error(f"Field analysis failed for connection {connection_id}: {e}")
                schema_info["field_analysis"] = {"error": str(e)}
            
            # Store in Redis cache if available
            if self.redis_service and self.redis_service.is_connected:
                await self.redis_service.cache_schema(connection_id, schema_info, ttl=3600)
            
            # Store in memory cache
            self.schema_cache[connection_id] = schema_info
            self.cache_expiry[connection_id] = datetime.now() + self.cache_duration
            
            logger.info(f"Schema analysis completed for connection {connection_id}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to analyze schema for connection {connection_id}: {e}")
            return {
                "tables": {},
                "relationships": [],
                "statistics": {"error": str(e)},
                "analyzed_at": datetime.now().isoformat()
            }
    
    def _infer_relationships(self, tables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Infer relationships based on naming patterns"""
        relationships = []
        
        for table_name, table_info in tables.items():
            for column in table_info["columns"]:
                column_name = column["name"].lower()
                
                # Look for common FK patterns like table_id, tableid
                if column_name.endswith("_id") or column_name.endswith("id"):
                    # Extract potential table name
                    if column_name.endswith("_id"):
                        potential_table = column_name[:-3]  # Remove _id
                    elif column_name != "id" and column_name.endswith("id"):
                        potential_table = column_name[:-2]  # Remove id
                    else:
                        continue
                    
                    # Check if table exists (handle singular/plural)
                    for target_table in tables.keys():
                        target_lower = target_table.lower()
                        if (target_lower == potential_table or 
                            target_lower == potential_table + "s" or 
                            target_lower == potential_table + "es" or
                            (potential_table.endswith("s") and target_lower == potential_table[:-1])):
                            
                            # Inferred relationship
                            relationships.append({
                                "from_table": table_name,
                                "from_column": column["name"],
                                "to_table": target_table,
                                "to_column": "id",  # Assume primary key is 'id'
                                "type": "inferred",
                                "confidence": 0.8
                            })
                            break
        
        return relationships