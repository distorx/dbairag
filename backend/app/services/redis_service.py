"""Redis caching service for improved performance"""
import json
import pickle
from typing import Optional, Any, Union
import redis.asyncio as redis
from redis.asyncio import Redis
from datetime import timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.is_connected = False
        
    async def connect(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=False  # We'll handle encoding/decoding ourselves
            )
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """Generate a cache key with prefix"""
        return f"dbairag:{prefix}:{identifier}"
    
    def _hash_key(self, data: str) -> str:
        """Generate hash for complex keys"""
        return hashlib.md5(data.encode()).hexdigest()
    
    async def get(self, key: str, prefix: str = "general") -> Optional[Any]:
        """Get value from cache"""
        if not self.is_connected:
            return None
            
        try:
            full_key = self._generate_key(prefix, key)
            value = await self.redis_client.get(full_key)
            
            if value:
                # Try to deserialize as JSON first, then pickle
                try:
                    return json.loads(value)
                except:
                    return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        prefix: str = "general",
        ttl: Optional[int] = 3600  # Default 1 hour
    ) -> bool:
        """Set value in cache with optional TTL"""
        if not self.is_connected:
            return False
            
        try:
            full_key = self._generate_key(prefix, key)
            
            # Serialize value
            try:
                serialized = json.dumps(value)
            except:
                serialized = pickle.dumps(value)
            
            if ttl:
                await self.redis_client.setex(full_key, ttl, serialized)
            else:
                await self.redis_client.set(full_key, serialized)
            
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str, prefix: str = "general") -> bool:
        """Delete value from cache"""
        if not self.is_connected:
            return False
            
        try:
            full_key = self._generate_key(prefix, key)
            result = await self.redis_client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.is_connected:
            return 0
            
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis delete pattern error: {e}")
            return 0
    
    # Specific cache methods for our application
    
    async def cache_schema(
        self, 
        connection_id: str, 
        schema_data: dict,
        ttl: int = 3600  # 1 hour default
    ) -> bool:
        """Cache database schema for a connection"""
        return await self.set(
            connection_id,
            schema_data,
            prefix="schema",
            ttl=ttl
        )
    
    async def get_cached_schema(self, connection_id: str) -> Optional[dict]:
        """Get cached database schema"""
        return await self.get(connection_id, prefix="schema")
    
    async def cache_enum_context(
        self,
        connection_id: str,
        enum_data: dict,
        ttl: int = 7200  # 2 hours default
    ) -> bool:
        """Cache enum context for a connection"""
        return await self.set(
            connection_id,
            enum_data,
            prefix="enums",
            ttl=ttl
        )
    
    async def get_cached_enum_context(self, connection_id: str) -> Optional[dict]:
        """Get cached enum context"""
        return await self.get(connection_id, prefix="enums")
    
    async def cache_sql_generation(
        self,
        prompt: str,
        connection_id: str,
        sql: str,
        ttl: int = 1800  # 30 minutes default
    ) -> bool:
        """Cache generated SQL for a prompt"""
        cache_key = self._hash_key(f"{connection_id}:{prompt}")
        return await self.set(
            cache_key,
            {"sql": sql, "prompt": prompt},
            prefix="sql",
            ttl=ttl
        )
    
    async def get_cached_sql(self, prompt: str, connection_id: str) -> Optional[str]:
        """Get cached SQL for a prompt"""
        cache_key = self._hash_key(f"{connection_id}:{prompt}")
        result = await self.get(cache_key, prefix="sql")
        return result.get("sql") if result else None
    
    async def cache_query_result(
        self,
        sql: str,
        connection_id: str,
        result: Any,
        ttl: int = 600  # 10 minutes default
    ) -> bool:
        """Cache query execution results"""
        cache_key = self._hash_key(f"{connection_id}:{sql}")
        return await self.set(
            cache_key,
            result,
            prefix="query_result",
            ttl=ttl
        )
    
    async def get_cached_query_result(self, sql: str, connection_id: str) -> Optional[Any]:
        """Get cached query result"""
        cache_key = self._hash_key(f"{connection_id}:{sql}")
        return await self.get(cache_key, prefix="query_result")
    
    async def invalidate_connection_cache(self, connection_id: str):
        """Invalidate all caches for a connection"""
        patterns = [
            f"dbairag:schema:{connection_id}",
            f"dbairag:enums:{connection_id}",
            f"dbairag:sql:*{connection_id}*",
            f"dbairag:query_result:*{connection_id}*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} cache entries for connection {connection_id}")
        return total_deleted
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        if not self.is_connected:
            return {"connected": False}
        
        try:
            info = await self.redis_client.info("stats")
            memory = await self.redis_client.info("memory")
            
            # Count keys by prefix
            schema_keys = 0
            enum_keys = 0
            sql_keys = 0
            result_keys = 0
            docs_keys = 0
            hints_keys = 0
            patterns_keys = 0
            
            async for key in self.redis_client.scan_iter(match="dbairag:*"):
                key_str = key.decode() if isinstance(key, bytes) else key
                if "schema:" in key_str:
                    schema_keys += 1
                elif "enums:" in key_str:
                    enum_keys += 1
                elif "sql:" in key_str:
                    sql_keys += 1
                elif "query_result:" in key_str:
                    result_keys += 1
                elif "docs:" in key_str or "documentation:" in key_str:
                    docs_keys += 1
                elif "hints:" in key_str:
                    hints_keys += 1
                elif "patterns:" in key_str:
                    patterns_keys += 1
            
            return {
                "connected": True,
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                    if info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0) > 0
                    else 0
                ),
                "used_memory_human": memory.get("used_memory_human", "0B"),
                "cached_keys": {
                    "schemas": schema_keys + docs_keys,  # Combine docs with schemas
                    "enums": enum_keys + hints_keys,     # Combine hints with enums
                    "sql_queries": sql_keys + patterns_keys,  # Combine patterns with sql
                    "query_results": result_keys
                }
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}

# Global instance
redis_service = RedisService()