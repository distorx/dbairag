"""
Test endpoint for demonstrating fuzzy matching capabilities
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from ..services.dynamic_fuzzy_matcher import DynamicFuzzyMatcher
from ..services.field_analyzer_service import FieldAnalyzerService

router = APIRouter(prefix="/api/fuzzy", tags=["fuzzy"])

class FuzzyTestRequest(BaseModel):
    query: str
    available_tables: List[str] = [
        "students", 
        "scholashipapplications",  # Note the typo in actual table name
        "scholarships",
        "courses",
        "enrollments",
        "professors"
    ]

class FuzzyTestResponse(BaseModel):
    original_query: str
    extracted_terms: List[str]
    table_matches: Dict[str, str]
    spelling_corrections: List[Dict[str, Any]]
    suggested_query: str = None
    confidence_score: float = 0.0
    soundex_codes: Dict[str, str]

@router.post("/test", response_model=FuzzyTestResponse)
async def test_fuzzy_matching(request: FuzzyTestRequest):
    """
    Test dynamic fuzzy matching capabilities with a query.
    The fuzzy matcher learns from the actual database schema.
    
    Example queries to test:
    - "count all studnet with aplication" (misspelled)
    - "show me scholership aplications" (misspelled)
    - "list studants enrolled in corses" (misspelled)
    """
    fuzzy_matcher = DynamicFuzzyMatcher()
    
    # Simulate learning from schema (in production this happens when schema is loaded)
    mock_schema = {
        "tables": {
            table: {"columns": []} for table in request.available_tables
        }
    }
    fuzzy_matcher.learn_from_schema(mock_schema)
    
    # Get suggestions from the dynamic fuzzy matcher
    suggestions = fuzzy_matcher.suggest_query_corrections(request.query)
    
    # Extract soundex codes for demonstration
    words = [w for w in request.query.lower().split() if len(w) > 2]
    soundex_codes = {word: fuzzy_matcher.soundex(word) for word in words[:5]}  # Limit to 5 words
    
    return FuzzyTestResponse(
        original_query=request.query,
        extracted_terms=list(suggestions.get("table_suggestions", {}).keys()),
        table_matches=suggestions.get("table_suggestions", {}),
        spelling_corrections=[],  # Dynamic matcher doesn't use this format
        suggested_query=suggestions.get("suggested_query"),
        confidence_score=max(suggestions.get("confidence_scores", {}).values()) if suggestions.get("confidence_scores") else 0.0,
        soundex_codes=soundex_codes
    )

@router.post("/match-single")
async def test_single_match(term: str, candidates: List[str] = None):
    """
    Test dynamic fuzzy matching for a single term against candidates.
    """
    if candidates is None:
        candidates = ["students", "scholashipapplications", "scholarships", "courses", "enrollments"]
    
    fuzzy_matcher = DynamicFuzzyMatcher()
    # Learn from the candidates
    mock_schema = {"tables": {table: {"columns": []} for table in candidates}}
    fuzzy_matcher.learn_from_schema(mock_schema)
    
    result = fuzzy_matcher.find_best_table_match(term, threshold=50)
    
    if result:
        match, score = result
        return {
            "term": term,
            "best_match": match,
            "score": score,
            "soundex": fuzzy_matcher.soundex(term),
            "match_soundex": fuzzy_matcher.soundex(match),
            "learned_patterns": fuzzy_matcher.learned_mappings.get(term.lower(), [])
        }
    else:
        return {
            "term": term,
            "best_match": None,
            "score": 0,
            "soundex": fuzzy_matcher.soundex(term),
            "message": "No match found above threshold"
        }

@router.get("/learned-patterns")
async def get_learned_patterns(tables: List[str] = None):
    """
    Get the patterns learned from a database schema.
    """
    if tables is None:
        tables = ["students", "scholashipapplications", "scholarships", "courses", "enrollments"]
    
    fuzzy_matcher = DynamicFuzzyMatcher()
    mock_schema = {"tables": {table: {"columns": []} for table in tables}}
    fuzzy_matcher.learn_from_schema(mock_schema)
    
    return {
        "compound_tables": fuzzy_matcher.compound_tables,
        "learned_mappings": fuzzy_matcher.learned_mappings,
        "table_patterns": fuzzy_matcher.table_patterns,
        "actual_tables": fuzzy_matcher.actual_tables
    }