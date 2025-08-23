"""API endpoints for query hints and patterns"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from ..database import get_db
from ..services.hint_service import hint_service
from ..services.redis_service import redis_service

router = APIRouter(prefix="/api/hints", tags=["hints"])

# Initialize Redis service for hint service
hint_service.set_redis_service(redis_service)

class HintCreate(BaseModel):
    category: str
    keywords: List[str]
    example_query: str
    sql_pattern: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class HintUpdate(BaseModel):
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    example_query: Optional[str] = None
    sql_pattern: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class PatternCreate(BaseModel):
    pattern_type: str
    natural_language: str
    sql_template: str
    parameters: Optional[dict] = None

class SuggestionRequest(BaseModel):
    user_input: str
    limit: Optional[int] = 10

@router.get("/")
async def get_hints(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all hints, optionally filtered by category"""
    hints = await hint_service.get_hints(db, category=category)
    return hints

@router.post("/")
async def create_hint(
    hint: HintCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new hint"""
    new_hint = await hint_service.add_hint(
        db,
        category=hint.category,
        keywords=hint.keywords,
        example_query=hint.example_query,
        sql_pattern=hint.sql_pattern,
        description=hint.description,
        tags=hint.tags
    )
    
    return {
        "id": new_hint.id,
        "message": "Hint created successfully"
    }

@router.put("/{hint_id}")
async def update_hint(
    hint_id: int,
    hint: HintUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing hint"""
    update_data = hint.dict(exclude_unset=True)
    updated_hint = await hint_service.update_hint(db, hint_id, **update_data)
    
    if not updated_hint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hint not found"
        )
    
    return {
        "id": updated_hint.id,
        "message": "Hint updated successfully"
    }

@router.post("/popularity/{hint_id}")
async def increment_popularity(
    hint_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Increment hint popularity (called when hint is used)"""
    await hint_service.increment_hint_popularity(db, hint_id)
    return {"message": "Popularity incremented"}

@router.get("/patterns")
async def get_patterns(
    pattern_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get query patterns, optionally filtered by type"""
    patterns = await hint_service.get_patterns(db, pattern_type=pattern_type)
    return patterns

@router.post("/patterns")
async def create_pattern(
    pattern: PatternCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new query pattern"""
    new_pattern = await hint_service.add_pattern(
        db,
        pattern_type=pattern.pattern_type,
        natural_language=pattern.natural_language,
        sql_template=pattern.sql_template,
        parameters=pattern.parameters
    )
    
    return {
        "id": new_pattern.id,
        "message": "Pattern created successfully"
    }

@router.post("/suggestions")
async def get_suggestions(
    request: SuggestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get intelligent suggestions based on user input"""
    suggestions = await hint_service.get_suggestions(
        db,
        user_input=request.user_input,
        limit=request.limit
    )
    return suggestions

@router.post("/learn")
async def learn_from_history(
    limit: Optional[int] = 100,
    db: AsyncSession = Depends(get_db)
):
    """Analyze query history to identify new patterns"""
    suggestions = await hint_service.learn_from_history(db, limit=limit)
    return {
        "patterns_found": len(suggestions),
        "suggestions": suggestions
    }

@router.post("/initialize")
async def initialize_hints(
    db: AsyncSession = Depends(get_db)
):
    """Initialize database with default hints"""
    await hint_service.initialize_default_hints(db)
    return {"message": "Default hints initialized"}

@router.post("/cache/invalidate")
async def invalidate_cache():
    """Invalidate all hints and patterns cache"""
    
    if not redis_service.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis cache not available"
        )
    
    hints_deleted = await hint_service.invalidate_hints_cache()
    patterns_deleted = await hint_service.invalidate_patterns_cache()
    
    return {
        "message": "Cache invalidated",
        "hints_deleted": hints_deleted,
        "patterns_deleted": patterns_deleted
    }

@router.post("/cache/warm")
async def warm_cache(
    db: AsyncSession = Depends(get_db)
):
    """Pre-load hints and patterns into cache"""
    
    if not redis_service.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis cache not available"
        )
    
    # Load all hints
    hints = await hint_service.get_hints(db, use_cache=False)
    
    # Load all patterns
    patterns = await hint_service.get_patterns(db, use_cache=False)
    
    return {
        "message": "Cache warmed",
        "hints_loaded": len(hints),
        "patterns_loaded": len(patterns)
    }

@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """Get all available hint categories"""
    from sqlalchemy import select, distinct
    from ..models import QueryHint
    
    result = await db.execute(
        select(distinct(QueryHint.category))
        .where(QueryHint.is_active == True)
        .order_by(QueryHint.category)
    )
    categories = result.scalars().all()
    
    return categories

@router.get("/stats")
async def get_hint_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about hints and patterns usage"""
    from sqlalchemy import select, func
    from ..models import QueryHint, QueryPattern
    
    # Count hints
    hint_count = await db.execute(select(func.count(QueryHint.id)))
    total_hints = hint_count.scalar()
    
    # Count patterns
    pattern_count = await db.execute(select(func.count(QueryPattern.id)))
    total_patterns = pattern_count.scalar()
    
    # Get most popular hints
    popular_hints = await db.execute(
        select(QueryHint)
        .order_by(QueryHint.popularity.desc())
        .limit(5)
    )
    top_hints = [
        {
            "id": h.id,
            "category": h.category,
            "example": h.example_query,
            "popularity": h.popularity
        }
        for h in popular_hints.scalars().all()
    ]
    
    # Get most used patterns
    used_patterns = await db.execute(
        select(QueryPattern)
        .order_by(QueryPattern.usage_count.desc())
        .limit(5)
    )
    top_patterns = [
        {
            "id": p.id,
            "type": p.pattern_type,
            "natural_language": p.natural_language,
            "usage_count": p.usage_count,
            "success_rate": p.success_rate
        }
        for p in used_patterns.scalars().all()
    ]
    
    return {
        "total_hints": total_hints,
        "total_patterns": total_patterns,
        "top_hints": top_hints,
        "top_patterns": top_patterns,
        "cache_status": "connected" if redis_service.is_connected else "disconnected"
    }