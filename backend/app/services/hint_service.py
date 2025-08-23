"""Service for managing query hints and patterns"""
from typing import List, Dict, Any, Optional
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from ..models import QueryHint, QueryPattern, QueryHistory
import logging

logger = logging.getLogger(__name__)

class HintService:
    def __init__(self):
        self.redis_service = None
        self.hints_cache = {}
        self.patterns_cache = {}
    
    def set_redis_service(self, redis_service):
        """Set Redis service for caching"""
        self.redis_service = redis_service
    
    async def get_hints(
        self, 
        db: AsyncSession,
        category: Optional[str] = None,
        active_only: bool = True,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Get query hints, optionally filtered by category"""
        
        cache_key = f"hints:{category or 'all'}"
        
        # Check Redis cache first
        if use_cache and self.redis_service and self.redis_service.is_connected:
            cached_hints = await self.redis_service.get(cache_key, prefix="hints")
            if cached_hints:
                logger.info(f"Hints loaded from Redis cache for category: {category or 'all'}")
                return cached_hints
        
        # Query database
        query = select(QueryHint)
        if active_only:
            query = query.where(QueryHint.is_active == True)
        if category:
            query = query.where(QueryHint.category == category)
        query = query.order_by(QueryHint.popularity.desc())
        
        result = await db.execute(query)
        hints = result.scalars().all()
        
        # Convert to dict format
        hints_list = []
        for hint in hints:
            hint_dict = {
                "id": hint.id,
                "category": hint.category,
                "keywords": json.loads(hint.keywords) if hint.keywords else [],
                "example": hint.example_query,
                "sql_pattern": hint.sql_pattern,
                "description": hint.description,
                "tags": json.loads(hint.tags) if hint.tags else [],
                "popularity": hint.popularity
            }
            hints_list.append(hint_dict)
        
        # Cache in Redis
        if self.redis_service and self.redis_service.is_connected:
            from ..config import settings
            await self.redis_service.set(
                cache_key,
                hints_list,
                prefix="hints",
                ttl=86400  # 24 hours
            )
            logger.info(f"Hints cached in Redis for category: {category or 'all'}")
        
        return hints_list
    
    async def add_hint(
        self,
        db: AsyncSession,
        category: str,
        keywords: List[str],
        example_query: str,
        sql_pattern: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> QueryHint:
        """Add a new query hint"""
        
        hint = QueryHint(
            category=category,
            keywords=json.dumps(keywords),
            example_query=example_query,
            sql_pattern=sql_pattern,
            description=description,
            tags=json.dumps(tags) if tags else None,
            popularity=0,
            is_active=True
        )
        
        db.add(hint)
        await db.commit()
        await db.refresh(hint)
        
        # Invalidate caches
        await self.invalidate_hints_cache()
        await self.invalidate_categories_cache()
        
        return hint
    
    async def update_hint(
        self,
        db: AsyncSession,
        hint_id: int,
        **kwargs
    ) -> Optional[QueryHint]:
        """Update an existing hint"""
        
        result = await db.execute(
            select(QueryHint).where(QueryHint.id == hint_id)
        )
        hint = result.scalar_one_or_none()
        
        if not hint:
            return None
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(hint, key):
                if key in ['keywords', 'tags'] and isinstance(value, list):
                    value = json.dumps(value)
                setattr(hint, key, value)
        
        await db.commit()
        await db.refresh(hint)
        
        # Invalidate caches
        await self.invalidate_hints_cache()
        await self.invalidate_categories_cache()
        
        return hint
    
    async def increment_hint_popularity(
        self,
        db: AsyncSession,
        hint_id: int
    ):
        """Increment the popularity counter for a hint"""
        
        await db.execute(
            update(QueryHint)
            .where(QueryHint.id == hint_id)
            .values(popularity=QueryHint.popularity + 1)
        )
        await db.commit()
    
    async def get_patterns(
        self,
        db: AsyncSession,
        pattern_type: Optional[str] = None,
        active_only: bool = True,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Get query patterns, optionally filtered by type"""
        
        cache_key = f"patterns:{pattern_type or 'all'}"
        
        # Check Redis cache first
        if use_cache and self.redis_service and self.redis_service.is_connected:
            cached_patterns = await self.redis_service.get(cache_key, prefix="patterns")
            if cached_patterns:
                logger.info(f"Patterns loaded from Redis cache for type: {pattern_type or 'all'}")
                return cached_patterns
        
        # Query database
        query = select(QueryPattern)
        if active_only:
            query = query.where(QueryPattern.is_active == True)
        if pattern_type:
            query = query.where(QueryPattern.pattern_type == pattern_type)
        query = query.order_by(QueryPattern.usage_count.desc())
        
        result = await db.execute(query)
        patterns = result.scalars().all()
        
        # Convert to dict format
        patterns_list = []
        for pattern in patterns:
            pattern_dict = {
                "id": pattern.id,
                "type": pattern.pattern_type,
                "natural_language": pattern.natural_language,
                "sql_template": pattern.sql_template,
                "parameters": json.loads(pattern.parameters) if pattern.parameters else {},
                "usage_count": pattern.usage_count,
                "success_rate": pattern.success_rate,
                "avg_execution_time": pattern.avg_execution_time
            }
            patterns_list.append(pattern_dict)
        
        # Cache in Redis
        if self.redis_service and self.redis_service.is_connected:
            await self.redis_service.set(
                cache_key,
                patterns_list,
                prefix="patterns",
                ttl=86400  # 24 hours
            )
            logger.info(f"Patterns cached in Redis for type: {pattern_type or 'all'}")
        
        return patterns_list
    
    async def add_pattern(
        self,
        db: AsyncSession,
        pattern_type: str,
        natural_language: str,
        sql_template: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> QueryPattern:
        """Add a new query pattern"""
        
        pattern = QueryPattern(
            pattern_type=pattern_type,
            natural_language=natural_language,
            sql_template=sql_template,
            parameters=json.dumps(parameters) if parameters else None,
            usage_count=0,
            success_rate=100,
            avg_execution_time=0,
            is_active=True
        )
        
        db.add(pattern)
        await db.commit()
        await db.refresh(pattern)
        
        # Invalidate cache
        await self.invalidate_patterns_cache()
        
        return pattern
    
    async def update_pattern_stats(
        self,
        db: AsyncSession,
        pattern_id: int,
        execution_time: int,
        success: bool
    ):
        """Update pattern usage statistics"""
        
        result = await db.execute(
            select(QueryPattern).where(QueryPattern.id == pattern_id)
        )
        pattern = result.scalar_one_or_none()
        
        if pattern:
            # Update usage count
            pattern.usage_count += 1
            
            # Update success rate
            if success:
                pattern.success_rate = (
                    (pattern.success_rate * (pattern.usage_count - 1) + 100) 
                    / pattern.usage_count
                )
            else:
                pattern.success_rate = (
                    (pattern.success_rate * (pattern.usage_count - 1)) 
                    / pattern.usage_count
                )
            
            # Update average execution time
            pattern.avg_execution_time = (
                (pattern.avg_execution_time * (pattern.usage_count - 1) + execution_time)
                / pattern.usage_count
            )
            
            await db.commit()
    
    async def learn_from_history(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Analyze query history to identify new patterns"""
        
        # Get recent successful queries
        result = await db.execute(
            select(QueryHistory)
            .where(QueryHistory.result_type != 'error')
            .order_by(QueryHistory.created_at.desc())
            .limit(limit)
        )
        history = result.scalars().all()
        
        # Analyze patterns
        patterns = {}
        for entry in history:
            prompt_lower = entry.prompt.lower()
            
            # Identify pattern type
            pattern_type = self._identify_pattern_type(prompt_lower)
            
            # Group by pattern
            if pattern_type not in patterns:
                patterns[pattern_type] = []
            
            patterns[pattern_type].append({
                "prompt": entry.prompt,
                "sql": entry.generated_sql,
                "execution_time": entry.execution_time
            })
        
        # Generate suggestions for new patterns
        suggestions = []
        for pattern_type, examples in patterns.items():
            if len(examples) >= 3:  # Need at least 3 examples to suggest a pattern
                suggestion = {
                    "pattern_type": pattern_type,
                    "examples": examples[:5],  # Top 5 examples
                    "suggested_template": self._generate_template(examples)
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _identify_pattern_type(self, prompt: str) -> str:
        """Identify the pattern type from a prompt"""
        
        if any(word in prompt for word in ['select', 'show', 'get', 'list']):
            if 'join' in prompt or 'with' in prompt:
                return 'join'
            elif any(word in prompt for word in ['count', 'sum', 'avg', 'max', 'min']):
                return 'aggregate'
            else:
                return 'select'
        elif any(word in prompt for word in ['insert', 'add', 'create']):
            return 'insert'
        elif any(word in prompt for word in ['update', 'modify', 'change']):
            return 'update'
        elif any(word in prompt for word in ['delete', 'remove']):
            return 'delete'
        else:
            return 'other'
    
    def _generate_template(self, examples: List[Dict[str, Any]]) -> str:
        """Generate a SQL template from examples"""
        
        if not examples:
            return ""
        
        # Simple template generation - can be enhanced with ML
        sql = examples[0]['sql']
        
        # Replace specific values with placeholders
        import re
        
        # Replace quoted strings
        sql = re.sub(r"'[^']*'", "'{{value}}'", sql)
        
        # Replace numbers
        sql = re.sub(r'\b\d+\b', '{{number}}', sql)
        
        # Replace table names (simplified)
        sql = re.sub(r'FROM\s+(\w+)', r'FROM {{table}}', sql)
        
        return sql
    
    async def invalidate_hints_cache(self):
        """Invalidate all hints cache in Redis"""
        
        if self.redis_service and self.redis_service.is_connected:
            deleted = await self.redis_service.delete_pattern("dbairag:hints:*")
            logger.info(f"Invalidated {deleted} hints cache entries")
            return deleted
        return 0
    
    async def invalidate_patterns_cache(self):
        """Invalidate all patterns cache in Redis"""
        
        if self.redis_service and self.redis_service.is_connected:
            deleted = await self.redis_service.delete_pattern("dbairag:patterns:*")
            logger.info(f"Invalidated {deleted} patterns cache entries")
            return deleted
        return 0
    
    async def invalidate_categories_cache(self):
        """Invalidate categories cache in Redis"""
        
        if self.redis_service and self.redis_service.is_connected:
            deleted = await self.redis_service.delete("hint_categories", prefix="hints")
            logger.info(f"Invalidated categories cache entry")
            return 1 if deleted else 0
        return 0
    
    async def get_suggestions(
        self,
        db: AsyncSession,
        user_input: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get intelligent suggestions based on user input"""
        
        input_lower = user_input.lower()
        suggestions = []
        
        # Get relevant hints
        hints = await self.get_hints(db)
        
        for hint in hints:
            # Check if any keyword matches
            keywords = hint.get('keywords', [])
            if any(keyword in input_lower for keyword in keywords):
                suggestions.append({
                    "type": "hint",
                    "category": hint['category'],
                    "suggestion": hint['example'],
                    "sql_pattern": hint['sql_pattern'],
                    "score": hint['popularity']
                })
        
        # Get relevant patterns
        patterns = await self.get_patterns(db)
        
        for pattern in patterns:
            if pattern['natural_language'].lower() in input_lower:
                suggestions.append({
                    "type": "pattern",
                    "category": pattern['type'],
                    "suggestion": pattern['natural_language'],
                    "sql_pattern": pattern['sql_template'],
                    "score": pattern['usage_count']
                })
        
        # Sort by score and limit
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:limit]
    
    async def initialize_default_hints(self, db: AsyncSession):
        """Initialize database with default hints"""
        
        # Check if hints already exist
        result = await db.execute(select(func.count(QueryHint.id)))
        count = result.scalar()
        
        if count > 0:
            logger.info(f"Hints already initialized ({count} hints exist)")
            return
        
        # Default hints to add
        default_hints = [
            {
                "category": "filtering",
                "keywords": ["where", "filter", "only", "with"],
                "example_query": "Show only active users",
                "sql_pattern": "SELECT * FROM table WHERE is_active = 1",
                "tags": ["filter", "condition"]
            },
            {
                "category": "sorting",
                "keywords": ["order", "sort", "by", "ascending", "descending"],
                "example_query": "Sort by date newest first",
                "sql_pattern": "SELECT * FROM table ORDER BY date DESC",
                "tags": ["sort", "order"]
            },
            {
                "category": "limiting",
                "keywords": ["top", "first", "limit", "last"],
                "example_query": "Show top 10 records",
                "sql_pattern": "SELECT TOP 10 * FROM table",
                "tags": ["limit", "pagination"]
            },
            {
                "category": "aggregation",
                "keywords": ["count", "sum", "average", "max", "min", "total"],
                "example_query": "Count all users",
                "sql_pattern": "SELECT COUNT(*) FROM users",
                "tags": ["aggregate", "calculation"]
            },
            {
                "category": "grouping",
                "keywords": ["group", "by", "per", "each"],
                "example_query": "Sales per month",
                "sql_pattern": "SELECT MONTH(date) as month, SUM(amount) FROM sales GROUP BY MONTH(date)",
                "tags": ["group", "aggregate"]
            },
            {
                "category": "joining",
                "keywords": ["with", "include", "related", "associated", "join"],
                "example_query": "Users with their orders",
                "sql_pattern": "SELECT * FROM users JOIN orders ON users.id = orders.user_id",
                "tags": ["join", "relationship"]
            },
            {
                "category": "date_time",
                "keywords": ["today", "yesterday", "this month", "last year", "date"],
                "example_query": "Orders from today",
                "sql_pattern": "SELECT * FROM orders WHERE DATE(order_date) = CAST(GETDATE() AS DATE)",
                "tags": ["date", "temporal"]
            },
            {
                "category": "comparison",
                "keywords": ["greater", "less", "between", "equal", "more than"],
                "example_query": "Amount between 100 and 500",
                "sql_pattern": "SELECT * FROM table WHERE amount BETWEEN 100 AND 500",
                "tags": ["comparison", "range"]
            },
            {
                "category": "pattern_matching",
                "keywords": ["like", "contains", "starts with", "ends with", "search"],
                "example_query": "Names starting with 'A'",
                "sql_pattern": "SELECT * FROM users WHERE name LIKE 'A%'",
                "tags": ["pattern", "search"]
            },
            {
                "category": "null_handling",
                "keywords": ["empty", "null", "missing", "blank", "without"],
                "example_query": "Users without email",
                "sql_pattern": "SELECT * FROM users WHERE email IS NULL",
                "tags": ["null", "missing"]
            }
        ]
        
        # Add default hints
        for hint_data in default_hints:
            hint = QueryHint(
                category=hint_data["category"],
                keywords=json.dumps(hint_data["keywords"]),
                example_query=hint_data["example_query"],
                sql_pattern=hint_data["sql_pattern"],
                tags=json.dumps(hint_data.get("tags", [])),
                popularity=0,
                is_active=True
            )
            db.add(hint)
        
        await db.commit()
        logger.info(f"Initialized {len(default_hints)} default hints")
        
        # Invalidate caches
        await self.invalidate_hints_cache()
        await self.invalidate_categories_cache()

# Global instance
hint_service = HintService()