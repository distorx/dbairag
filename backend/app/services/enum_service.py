"""Service for managing database-specific enums"""
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

class EnumService:
    def __init__(self):
        self.enums_cache: Dict[str, Dict[str, Any]] = {}
        self.redis_service = None
    
    def set_redis_service(self, redis_service):
        """Set Redis service for caching"""
        self.redis_service = redis_service
        
    async def load_enums_from_file(self, file_path: str, connection_id: str) -> bool:
        """Load enums from a JSON file for a specific connection"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
                
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Store enums for this connection
            self.enums_cache[connection_id] = data.get("enums", {})
            return True
            
        except Exception as e:
            print(f"Error loading enums: {e}")
            return False
    
    async def get_enum_context(self, connection_id: str) -> str:
        """Get enum information as context for SQL generation"""
        
        # Check Redis cache first if available
        if self.redis_service and self.redis_service.is_connected:
            cached_context = await self.redis_service.get(f"enum_context:{connection_id}", prefix="enums")
            if cached_context:
                logger.info(f"Enum context loaded from Redis cache for connection {connection_id}")
                return cached_context
        
        # Check memory cache
        if connection_id not in self.enums_cache:
            return ""
            
        enums = self.enums_cache[connection_id]
        if not enums:
            return ""
            
        context_parts = ["\nDatabase Enums Information:"]
        
        for enum_name, enum_data in enums.items():
            context_parts.append(f"\n{enum_name}:")
            values = enum_data.get("values", {})
            
            for value_name, value_data in values.items():
                value = value_data.get("value", "")
                description = value_data.get("description", "")
                context_parts.append(f"  - {value_name} = {value}")
                if description:
                    context_parts.append(f"    Description: {description}")
        
        context = "\n".join(context_parts)
        
        # Cache in Redis if available
        if context and self.redis_service and self.redis_service.is_connected:
            from ..config import settings
            await self.redis_service.set(
                f"enum_context:{connection_id}",
                context,
                prefix="enums",
                ttl=settings.cache_ttl_enums
            )
            logger.info(f"Enum context cached in Redis for connection {connection_id}")
        
        return context
    
    def translate_enum_in_query(self, query: str, connection_id: str) -> str:
        """Translate enum names to their numeric values in SQL query"""
        if connection_id not in self.enums_cache:
            return query
            
        enums = self.enums_cache[connection_id]
        modified_query = query
        
        for enum_name, enum_data in enums.items():
            values = enum_data.get("values", {})
            
            for value_name, value_data in values.items():
                numeric_value = value_data.get("value", "")
                
                # Replace enum name with numeric value in query
                # Handle different SQL patterns
                patterns = [
                    f"'{value_name}'",  # String literal
                    f'"{value_name}"',  # Double quoted
                    f"= {value_name}",  # Direct comparison
                    f"IN ({value_name}",  # IN clause
                    f", {value_name}",  # List item
                ]
                
                for pattern in patterns:
                    if pattern in modified_query:
                        replacement = pattern.replace(value_name, str(numeric_value))
                        modified_query = modified_query.replace(pattern, replacement)
        
        return modified_query
    
    def get_enum_suggestions(self, connection_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get enum suggestions for frontend dropdown/autocomplete"""
        if connection_id not in self.enums_cache:
            return {}
            
        enums = self.enums_cache[connection_id]
        suggestions = {}
        
        for enum_name, enum_data in enums.items():
            values = enum_data.get("values", {})
            enum_options = []
            
            for value_name, value_data in values.items():
                option = {
                    "label": value_name,
                    "value": value_data.get("value", 0),
                    "description": value_data.get("description", "")
                }
                enum_options.append(option)
            
            suggestions[enum_name] = enum_options
        
        return suggestions
    
    async def load_enums_from_database(self, db: AsyncSession, connection_id: int) -> bool:
        """Load all active enum files for a connection from database"""
        try:
            from ..models import EnumFile
            
            # Get all active enum files for this connection
            result = await db.execute(
                select(EnumFile).where(
                    EnumFile.connection_id == connection_id,
                    EnumFile.is_active == True
                )
            )
            enum_files = result.scalars().all()
            
            # Clear existing enums for this connection
            str_connection_id = str(connection_id)
            self.enums_cache[str_connection_id] = {}
            
            # Merge all enum files
            for enum_file in enum_files:
                try:
                    # Parse the cached JSON content
                    file_data = json.loads(enum_file.content_json)
                    
                    # If the JSON has an "enums" key, use it; otherwise treat the whole object as enums
                    if "enums" in file_data:
                        enums_data = file_data["enums"]
                    else:
                        enums_data = file_data
                    
                    # Merge with existing enums for this connection
                    if str_connection_id not in self.enums_cache:
                        self.enums_cache[str_connection_id] = {}
                    
                    # Add source file information to each enum
                    for enum_name, enum_values in enums_data.items():
                        if "source_file" not in enum_values:
                            enum_values["source_file"] = enum_file.original_filename
                        self.enums_cache[str_connection_id][enum_name] = enum_values
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing enum file {enum_file.original_filename}: {e}")
                    continue
            
            # Cache enums in Redis if available
            if self.redis_service and self.redis_service.is_connected:
                from ..config import settings
                await self.redis_service.cache_enum_context(
                    str_connection_id,
                    self.enums_cache[str_connection_id],
                    ttl=settings.cache_ttl_enums
                )
                logger.info(f"Enums cached in Redis for connection {str_connection_id}")
            
            return True
            
        except Exception as e:
            print(f"Error loading enums from database: {e}")
            return False
    
    def explain_enum_usage(self, enum_name: str, connection_id: str) -> str:
        """Explain how to use a specific enum in queries"""
        if connection_id not in self.enums_cache:
            return f"No enum information available for this connection."
            
        enums = self.enums_cache[connection_id]
        
        if enum_name not in enums:
            return f"Enum '{enum_name}' not found. Available enums: {', '.join(enums.keys())}"
        
        enum_data = enums[enum_name]
        values = enum_data.get("values", {})
        source_file = enum_data.get("source_file", "Unknown")
        
        explanation = [
            f"\nEnum: {enum_name}",
            f"Source: {source_file}",
            "\nValues:"
        ]
        
        for value_name, value_data in values.items():
            value = value_data.get("value", "")
            description = value_data.get("description", "")
            explanation.append(f"  • {value_name} ({value})")
            if description:
                explanation.append(f"    {description}")
        
        explanation.extend([
            "\nUsage Examples:",
            f"  SELECT * FROM table WHERE status = {list(values.values())[0].get('value', 0)}  -- {list(values.keys())[0]}",
            f"  SELECT * FROM table WHERE status IN ({', '.join(str(v.get('value', 0)) for v in list(values.values())[:3])})",
            "\nNote: Use numeric values in SQL queries, not the enum names."
        ])
        
        return "\n".join(explanation)

# Global instance
enum_service = EnumService()