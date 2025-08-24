"""
MongoDB-based hints storage service for learning and persisting query patterns
"""
import logging
import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

class HintsStorageService:
    """Service for storing and retrieving query hints using MongoDB"""
    
    def __init__(self, mongodb_url: str = "mongodb://distorx.com:27017/"):
        self.mongodb_url = mongodb_url
        self.client = None
        self.db = None
        self.hints_collection = None
        self.query_history_collection = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client.rag_sql_hints
            self.hints_collection = self.db.query_hints
            self.query_history_collection = self.db.query_history
            
            # Create indexes for better performance
            await self.hints_collection.create_index([("pattern_hash", ASCENDING)], unique=True)
            await self.hints_collection.create_index([("usage_count", DESCENDING)])
            await self.hints_collection.create_index([("success_rate", DESCENDING)])
            await self.hints_collection.create_index([("category", ASCENDING)])
            await self.hints_collection.create_index([("created_at", DESCENDING)])
            
            await self.query_history_collection.create_index([("connection_id", ASCENDING)])
            await self.query_history_collection.create_index([("created_at", DESCENDING)])
            
            logger.info("✅ Connected to MongoDB for hints storage")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def _generate_pattern_hash(self, sql_query: str) -> str:
        """Generate a unique hash for a SQL pattern"""
        # Normalize the SQL query to create a pattern
        pattern = self._normalize_sql_pattern(sql_query)
        return hashlib.md5(pattern.encode()).hexdigest()
    
    def _normalize_sql_pattern(self, sql_query: str) -> str:
        """Normalize SQL query to extract the pattern"""
        # Remove specific values and normalize to pattern
        pattern = sql_query.upper()
        
        # Replace specific numbers with placeholders
        pattern = re.sub(r'\b\d+\b', 'N', pattern)
        
        # Replace quoted strings with placeholders
        pattern = re.sub(r"'[^']*'", "'VALUE'", pattern)
        pattern = re.sub(r'"[^"]*"', '"VALUE"', pattern)
        
        # Replace table/column names in certain patterns
        pattern = re.sub(r'\bFROM\s+(\w+)', r'FROM TABLE', pattern)
        pattern = re.sub(r'\bJOIN\s+(\w+)', r'JOIN TABLE', pattern)
        
        # Remove extra whitespace
        pattern = ' '.join(pattern.split())
        
        return pattern
    
    def _categorize_query(self, sql_query: str) -> str:
        """Categorize SQL query based on its content"""
        sql_upper = sql_query.upper()
        
        if "WITH" in sql_upper and "AS (" in sql_upper:
            return "CTE"
        elif "OVER (" in sql_upper:
            return "Window Function"
        elif any(join in sql_upper for join in ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"]):
            return "JOIN"
        elif any(agg in sql_upper for agg in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX(", "GROUP BY"]):
            return "Aggregation"
        elif any(dt in sql_upper for dt in ["DATEADD", "DATEDIFF", "YEAR(", "MONTH(", "GETDATE()"]):
            return "Date/Time"
        elif any(adv in sql_upper for adv in ["PIVOT", "UNPIVOT", "MERGE", "FOR JSON", "STRING_AGG"]):
            return "Advanced"
        elif "SELECT" in sql_upper and "WHERE" in sql_upper:
            return "Filtered Select"
        elif "SELECT" in sql_upper:
            return "Basic Select"
        elif "INSERT" in sql_upper:
            return "Insert"
        elif "UPDATE" in sql_upper:
            return "Update"
        elif "DELETE" in sql_upper:
            return "Delete"
        else:
            return "Other"
    
    def _extract_query_name(self, prompt: str, sql_query: str) -> str:
        """Extract a meaningful name for the query pattern"""
        # Try to extract key action from prompt
        prompt_lower = prompt.lower()
        
        # Common patterns
        if "count" in prompt_lower:
            if "group" in prompt_lower or "by" in prompt_lower:
                return "Count grouped by category"
            elif "join" in sql_query.upper():
                return "Count with join"
            else:
                return "Count records"
        elif "average" in prompt_lower or "avg" in prompt_lower:
            return "Calculate average"
        elif "sum" in prompt_lower or "total" in prompt_lower:
            return "Calculate sum"
        elif "top" in prompt_lower or "first" in prompt_lower:
            return "Select top records"
        elif "recent" in prompt_lower or "latest" in prompt_lower:
            return "Get recent records"
        elif "between" in prompt_lower:
            return "Filter by range"
        elif "group" in prompt_lower:
            return "Group by category"
        elif "join" in sql_query.upper():
            return "Join tables"
        else:
            # Use first few words of prompt
            words = prompt.split()[:5]
            return ' '.join(words)
    
    async def save_successful_query(self, 
                                   prompt: str, 
                                   sql_query: str, 
                                   connection_id: str,
                                   execution_time_ms: float,
                                   result_count: int = 0) -> bool:
        """Save a successful query pattern to MongoDB"""
        try:
            pattern_hash = self._generate_pattern_hash(sql_query)
            category = self._categorize_query(sql_query)
            query_name = self._extract_query_name(prompt, sql_query)
            
            # Try to insert or update the hint
            existing = await self.hints_collection.find_one({"pattern_hash": pattern_hash})
            
            if existing:
                # Update existing pattern
                await self.hints_collection.update_one(
                    {"pattern_hash": pattern_hash},
                    {
                        "$inc": {"usage_count": 1, "success_count": 1},
                        "$push": {
                            "execution_times": {
                                "$each": [execution_time_ms],
                                "$slice": -100  # Keep last 100 execution times
                            }
                        },
                        "$set": {
                            "last_used": datetime.now(timezone.utc),
                            "avg_execution_time": {
                                "$avg": "$execution_times"
                            }
                        },
                        "$addToSet": {
                            "example_prompts": {
                                "$each": [prompt],
                                "$slice": -10  # Keep last 10 example prompts
                            }
                        }
                    }
                )
                logger.info(f"📈 Updated existing hint: {query_name}")
            else:
                # Create new hint
                hint_doc = {
                    "pattern_hash": pattern_hash,
                    "name": query_name,
                    "description": f"Auto-learned from: {prompt[:100]}",
                    "category": category,
                    "sql_template": sql_query,
                    "sql_pattern": self._normalize_sql_pattern(sql_query),
                    "example_prompts": [prompt],
                    "usage_count": 1,
                    "success_count": 1,
                    "success_rate": 100.0,
                    "avg_execution_time": execution_time_ms,
                    "execution_times": [execution_time_ms],
                    "connection_ids": [connection_id],
                    "created_at": datetime.now(timezone.utc),
                    "last_used": datetime.now(timezone.utc),
                    "auto_learned": True,
                    "complexity_score": self._calculate_complexity(sql_query)
                }
                
                await self.hints_collection.insert_one(hint_doc)
                logger.info(f"💡 Learned new hint: {query_name} ({category})")
            
            # Also save to query history for analysis
            await self.query_history_collection.insert_one({
                "prompt": prompt,
                "sql_query": sql_query,
                "connection_id": connection_id,
                "execution_time_ms": execution_time_ms,
                "result_count": result_count,
                "success": True,
                "created_at": datetime.now(timezone.utc)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save query hint: {e}")
            return False
    
    def _calculate_complexity(self, sql_query: str) -> float:
        """Calculate complexity score for a SQL query"""
        score = 1.0
        sql_upper = sql_query.upper()
        
        # Add complexity for various SQL features
        if "JOIN" in sql_upper:
            score += sql_upper.count("JOIN") * 0.5
        if "GROUP BY" in sql_upper:
            score += 0.3
        if "HAVING" in sql_upper:
            score += 0.3
        if "WITH" in sql_upper:
            score += 0.5
        if "OVER (" in sql_upper:
            score += 0.6
        if "PIVOT" in sql_upper:
            score += 0.7
        if "UNION" in sql_upper:
            score += 0.4
        if "CASE" in sql_upper:
            score += 0.2 * sql_upper.count("CASE")
        if "EXISTS" in sql_upper:
            score += 0.4
        
        # Subqueries
        score += sql_upper.count("(SELECT") * 0.4
        
        return min(score, 10.0)  # Cap at 10
    
    async def get_learned_hints(self, 
                               connection_id: Optional[str] = None,
                               category: Optional[str] = None,
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Get learned hints from MongoDB"""
        try:
            # Build query filter
            filter_query = {"auto_learned": True}
            if connection_id:
                filter_query["connection_ids"] = connection_id
            if category:
                filter_query["category"] = category
            
            # Get hints sorted by usage and success rate
            cursor = self.hints_collection.find(filter_query).sort([
                ("usage_count", DESCENDING),
                ("success_rate", DESCENDING)
            ]).limit(limit)
            
            hints = []
            async for hint in cursor:
                hints.append({
                    "name": hint.get("name"),
                    "description": hint.get("description"),
                    "category": hint.get("category"),
                    "template": hint.get("sql_template"),
                    "usage_count": hint.get("usage_count", 0),
                    "success_rate": hint.get("success_rate", 0),
                    "avg_execution_time": hint.get("avg_execution_time", 0),
                    "complexity_score": hint.get("complexity_score", 1),
                    "example_prompts": hint.get("example_prompts", [])[:3],
                    "last_used": hint.get("last_used")
                })
            
            return hints
            
        except Exception as e:
            logger.error(f"❌ Failed to get learned hints: {e}")
            return []
    
    async def get_popular_patterns(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular query patterns"""
        try:
            pipeline = [
                {"$match": {"usage_count": {"$gt": 1}}},
                {"$sort": {"usage_count": -1}},
                {"$limit": limit},
                {"$project": {
                    "_id": 0,
                    "name": 1,
                    "category": 1,
                    "template": "$sql_template",
                    "usage_count": 1,
                    "success_rate": 1,
                    "complexity_score": 1
                }}
            ]
            
            cursor = self.hints_collection.aggregate(pipeline)
            patterns = []
            async for pattern in cursor:
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Failed to get popular patterns: {e}")
            return []
    
    async def get_category_statistics(self) -> Dict[str, Any]:
        """Get statistics about learned patterns by category"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1},
                    "total_usage": {"$sum": "$usage_count"},
                    "avg_complexity": {"$avg": "$complexity_score"},
                    "avg_success_rate": {"$avg": "$success_rate"}
                }},
                {"$sort": {"total_usage": -1}}
            ]
            
            cursor = self.hints_collection.aggregate(pipeline)
            stats = {}
            async for stat in cursor:
                stats[stat["_id"]] = {
                    "pattern_count": stat["count"],
                    "total_usage": stat["total_usage"],
                    "avg_complexity": round(stat.get("avg_complexity", 0), 2),
                    "avg_success_rate": round(stat.get("avg_success_rate", 0), 2)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get category statistics: {e}")
            return {}
    
    async def search_hints(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for hints based on prompt examples or SQL content"""
        try:
            # Create text search query
            search_query = {
                "$or": [
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"description": {"$regex": search_term, "$options": "i"}},
                    {"example_prompts": {"$regex": search_term, "$options": "i"}},
                    {"sql_template": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            cursor = self.hints_collection.find(search_query).sort([
                ("usage_count", DESCENDING)
            ]).limit(limit)
            
            hints = []
            async for hint in cursor:
                hints.append({
                    "name": hint.get("name"),
                    "description": hint.get("description"),
                    "category": hint.get("category"),
                    "template": hint.get("sql_template"),
                    "usage_count": hint.get("usage_count", 0),
                    "complexity_score": hint.get("complexity_score", 1)
                })
            
            return hints
            
        except Exception as e:
            logger.error(f"❌ Failed to search hints: {e}")
            return []

# Global instance
hints_storage = HintsStorageService()