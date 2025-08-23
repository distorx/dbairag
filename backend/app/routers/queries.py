from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
import json
import time
import os
import uuid
from pathlib import Path
import aiofiles
import asyncio
import logging
from ..database import get_db
from ..models import Connection as ConnectionModel, QueryHistory, EnumFile
from ..schemas import (
    QueryRequest, QueryResponse, ResultType, QueryType,
    TableType, DataTypeCategory, QueryTemplate, QuerySuggestions,
    DatabaseSchema, TableInfo, ColumnInfo
)
from ..services import MSSQLService
from ..services.sqlcmd_service import sqlcmd_service
from ..services.schema_cache_service import schema_cache_service
from ..services.query_execution_service import QueryExecutionService
from ..services.rag_service import RAGService
from ..services.optimized_rag_service import optimized_rag_service
from ..services.schema_analyzer_universal import UniversalSchemaAnalyzer as SchemaAnalyzer
from ..services.enum_service import enum_service
from ..services.redis_service import redis_service
from ..services.documentation_service import documentation_service
from ..services.retry_service import RetryService, RetryConfig, QueryRetryWrapper
from ..services.queries_service import get_comprehensive_context, refresh_all_metadata
from ..services.schema_sync_service import SchemaSyncService
from ..utils.json_utils import safe_json_dumps

router = APIRouter(prefix="/api/queries", tags=["queries"])
logger = logging.getLogger(__name__)

rag_service = RAGService()
schema_analyzer = SchemaAnalyzer()
schema_sync_service = SchemaSyncService()

# Initialize Redis service for all services
schema_analyzer.set_redis_service(redis_service)
enum_service.set_redis_service(redis_service)
rag_service.set_redis_service(redis_service)

# Initialize retry service
retry_config = RetryConfig()
retry_service = RetryService(retry_config)
query_retry_wrapper = QueryRetryWrapper(retry_service)

@router.post("/execute-optimized", response_model=QueryResponse)
async def execute_query_optimized(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a natural language query using the optimized RAG service"""
    
    overall_start = time.time()
    logger.info(f"🚀 OPTIMIZED: Starting query execution for: '{request.prompt}'")
    
    # Get connection
    connection_start = time.time()
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == request.connection_id)
    )
    connection = result.scalar_one_or_none()
    connection_time = time.time() - connection_start
    logger.info(f"⏱️ OPTIMIZED: Connection lookup: {connection_time*1000:.2f}ms")
    
    if not connection:
        # Demo mode with optimized mock data
        if request.connection_id == 1:
            logger.info("🔧 OPTIMIZED: Using demo mode with optimized schema")
            
            # Minimal mock schema for pattern matching
            mock_schema = {
                "tables": {
                    "Students": {
                        "columns": [
                            {"name": "Id", "data_type": "int"},
                            {"name": "FirstName", "data_type": "nvarchar"},
                            {"name": "LastName", "data_type": "nvarchar"}
                        ],
                        "row_count": 307,
                        "foreign_keys": []
                    },
                    "ScholarshipApplications": {
                        "columns": [
                            {"name": "Id", "data_type": "int"},
                            {"name": "StudentId", "data_type": "int"},
                            {"name": "Status", "data_type": "nvarchar"}
                        ],
                        "row_count": 305,
                        "foreign_keys": [
                            {"column": "StudentId", "referenced_table": "Students", "referenced_column": "Id"}
                        ]
                    }
                }
            }
            
            # Use optimized RAG service
            sql_start = time.time()
            sql_query, metadata = await optimized_rag_service.generate_sql_optimized(
                request.prompt, mock_schema, "1"
            )
            sql_time = time.time() - sql_start
            logger.info(f"⏱️ OPTIMIZED: SQL generation: {sql_time*1000:.2f}ms")
            
            if not sql_query:
                error_msg = metadata.get("error", "Failed to generate SQL")
                return QueryResponse(
                    prompt=request.prompt,
                    generated_sql=None,
                    result_type=ResultType.ERROR,
                    result_data={"error": error_msg},
                    execution_time=int((time.time() - overall_start) * 1000)
                )
            
            # Mock execution for demo
            mock_exec_start = time.time()
            if "JOIN" in sql_query.upper():
                mock_result = {"columns": ["total"], "data": [{"total": 305}], "row_count": 1}
                logger.info("✅ OPTIMIZED: JOIN query detected, returning application count")
            else:
                mock_result = {"columns": ["total"], "data": [{"total": 307}], "row_count": 1}
                logger.info("✅ OPTIMIZED: Simple count query, returning total students")
            
            mock_exec_time = time.time() - mock_exec_start
            total_time = int((time.time() - overall_start) * 1000)
            
            # Log detailed performance metrics
            optimized_rag_service.log_performance_metrics(
                "demo_execution", 
                total_time, 
                {
                    **metadata,
                    "connection_time": f"{connection_time*1000:.2f}ms",
                    "sql_generation_time": f"{sql_time*1000:.2f}ms", 
                    "mock_execution_time": f"{mock_exec_time*1000:.2f}ms",
                    "total_time": f"{total_time}ms"
                }
            )
            
            logger.info(f"✅ OPTIMIZED: Demo query completed in {total_time}ms")
            
            return QueryResponse(
                prompt=request.prompt,
                generated_sql=sql_query,
                result_type=ResultType.TABLE,
                result_data=mock_result,
                execution_time=total_time,
                metadata=metadata
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
    
    # Real connection path with optimized performance
    logger.info(f"🔧 OPTIMIZED: Using real connection: {connection.name}")
    
    try:
        # Get schema with intelligent caching using Schema Cache Service
        schema_start = time.time()
        schema_info = await schema_cache_service.get_cached_schema(
            str(connection.id), connection.connection_string, force_refresh=False
        )
        schema_time = time.time() - schema_start
        logger.info(f"⚡ OPTIMIZED: Cached schema retrieval: {schema_time*1000:.2f}ms")
        
        # Generate SQL with optimized RAG
        sql_start = time.time()
        sql_query, metadata = await optimized_rag_service.generate_sql_optimized(
            request.prompt, schema_info, str(request.connection_id)
        )
        sql_time = time.time() - sql_start
        logger.info(f"⏱️ OPTIMIZED: SQL generation: {sql_time*1000:.2f}ms")
        
        if not sql_query:
            error_msg = metadata.get("error", "Failed to generate SQL")
            logger.error(f"❌ OPTIMIZED: SQL generation failed: {error_msg}")
            return QueryResponse(
                prompt=request.prompt,
                generated_sql=None,
                result_type=ResultType.ERROR,
                result_data={"error": error_msg},
                execution_time=int((time.time() - overall_start) * 1000),
                metadata=metadata
            )
        
        logger.info(f"🎯 OPTIMIZED: Generated SQL: {sql_query}")
        
        # Execute query with timing using SQLCmd service
        exec_start = time.time()
        query_result = await sqlcmd_service.execute_query(connection.connection_string, sql_query)
        exec_time = time.time() - exec_start
        logger.info(f"⏱️ OPTIMIZED: SQLCmd query execution: {exec_time*1000:.2f}ms")
        
        total_time = int((time.time() - overall_start) * 1000)
        
        # Log comprehensive performance metrics
        optimized_rag_service.log_performance_metrics(
            "real_execution", 
            total_time, 
            {
                **metadata,
                "connection_time": f"{connection_time*1000:.2f}ms",
                "schema_time": f"{schema_time*1000:.2f}ms",
                "sql_generation_time": f"{sql_time*1000:.2f}ms", 
                "query_execution_time": f"{exec_time*1000:.2f}ms",
                "total_time": f"{total_time}ms",
                "rows_returned": query_result.get("row_count", 0),
                "connection_name": connection.name
            }
        )
        
        logger.info(f"✅ OPTIMIZED: Real query completed in {total_time}ms with {query_result.get('row_count', 0)} rows")
        
        return QueryResponse(
            prompt=request.prompt,
            generated_sql=sql_query,
            result_type=ResultType.TABLE,
            result_data=query_result,
            execution_time=total_time,
            metadata=metadata
        )
        
    except Exception as e:
        error_time = int((time.time() - overall_start) * 1000)
        logger.error(f"❌ OPTIMIZED: Error after {error_time}ms: {str(e)}")
        
        # Return error with timing information
        return QueryResponse(
            prompt=request.prompt,
            generated_sql=None,
            result_type=ResultType.ERROR,
            result_data={"error": str(e)},
            execution_time=error_time,
            metadata={"method": "error", "error": str(e), "error_time": f"{error_time}ms"}
        )

@router.post("/execute", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a natural language query against a database with intelligent retry logic"""
    
    # Get connection
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == request.connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        # For testing/demo purposes, create a mock connection response
        # In production, this should raise an error
        if request.connection_id == 1:
            # Demo mode - generate SQL without actual connection
            # Create mock schema info for better pattern matching
            mock_schema_info = {
                "tables": {
                    "Students": {
                        "columns": [
                            {"name": "Id", "data_type": "int"},
                            {"name": "FirstName", "data_type": "nvarchar"},
                            {"name": "LastName", "data_type": "nvarchar"}
                        ],
                        "row_count": 307,
                        "foreign_keys": []
                    },
                    "ScholarshipApplications": {
                        "columns": [
                            {"name": "Id", "data_type": "int"},
                            {"name": "StudentId", "data_type": "int"},
                            {"name": "Status", "data_type": "nvarchar"}
                        ],
                        "row_count": 305,
                        "foreign_keys": [
                            {"column": "StudentId", "referenced_table": "Students", "referenced_column": "Id"}
                        ]
                    }
                }
            }
            sql_query, metadata = await rag_service.generate_sql(request.prompt, mock_schema_info, "1")
            
            if not sql_query:
                error_msg = metadata.get("error", "Failed to generate SQL")
                return QueryResponse(
                    prompt=request.prompt,
                    generated_sql=None,
                    result_type=ResultType.ERROR,
                    result_data={"error": error_msg},
                    execution_time=0
                )
            else:
                # Return the generated SQL without execution
                return QueryResponse(
                    prompt=request.prompt,
                    generated_sql=sql_query,
                    result_type=ResultType.TEXT,
                    result_data={"message": "SQL generated (no connection to execute)", "sql": sql_query},
                    execution_time=0
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
    
    if not connection.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection is not active"
        )
    
    start_time = time.time()
    
    try:
        # Store SQL query for table suggestions
        captured_sql_query = None
        
        # Execute query with intelligent retry and metadata refresh
        async def query_func():
            """Execute the actual query with comprehensive context"""
            nonlocal captured_sql_query
            
            # Skip schema sync during query execution - it should be done separately
            # This prevents query execution from hanging
            schema_info = None
            
            # Get comprehensive context (use synced schema if available)
            comprehensive_context = await get_comprehensive_context(
                schema_analyzer=schema_analyzer,
                enum_service=enum_service, 
                documentation_service=documentation_service,
                connection=connection,
                connection_id=str(connection.id),
                db=db,
                force_refresh=False  # Don't force refresh since we just synced
            )
            
            # Generate SQL from prompt using RAG with FULL context
            sql_query, metadata = await rag_service.generate_sql_with_full_context(
                request.prompt, 
                comprehensive_context, 
                str(connection.id)
            )
            
            # If we have enum translations, apply them
            if sql_query and connection.id:
                sql_query = enum_service.translate_enum_in_query(sql_query, str(connection.id))
            
            # Capture SQL for table suggestions
            captured_sql_query = sql_query
            
            if not sql_query:
                error_msg = metadata.get("error", "Failed to generate SQL")
                raise Exception(f"SQL Generation Error: {error_msg}")
            
            # Execute the SQL query with database type awareness
            df, error = await QueryExecutionService.execute_query_async(
                connection.connection_string,
                sql_query,
                connection.database_type
            )
            
            if error:
                raise Exception(f"SQL Execution Error: {error}")
            
            # Prepare result data
            result_type = metadata.get("result_type", ResultType.TABLE)
            
            if df is not None:
                # Convert DataFrame to dict for JSON serialization
                result_data = {
                    "columns": df.columns.tolist(),
                    "data": df.to_dict('records'),
                    "row_count": len(df)
                }
                
                # If it's a single value result, extract it
                if result_type == ResultType.TEXT and len(df) == 1 and len(df.columns) == 1:
                    result_data = str(df.iloc[0, 0])
            else:
                # Non-SELECT query result
                result_data = "Query executed successfully"
                result_type = ResultType.TEXT
            
            return {
                "sql_query": sql_query,
                "result_type": result_type,
                "result_data": result_data,
                "metadata": metadata
            }
        
        async def refresh_metadata_func():
            """Refresh all database metadata on errors"""
            refresh_results = await refresh_all_metadata(
                schema_analyzer=schema_analyzer,
                enum_service=enum_service,
                documentation_service=documentation_service,
                connection=connection,
                connection_id=str(connection.id),
                db=db
            )
            return refresh_results
        
        # Get schema info for table suggestions
        engine = schema_analyzer.create_engine(connection.connection_string)
        schema_info = await schema_analyzer.get_database_schema(
            engine, str(connection.id), force_refresh=False
        )
        
        # Execute with 10-second timeout and intelligent fallback
        try:
            result, retry_log = await asyncio.wait_for(
                retry_service.execute_with_retry(
                    query_func=query_func,
                    refresh_metadata_func=refresh_metadata_func,
                    context={"connection_id": str(connection.id), "prompt": request.prompt},
                    operation_name="RAG SQL Query",
                    schema_info=schema_info,
                    original_sql_query=captured_sql_query
                ),
                timeout=30.0  # 30 second timeout for query execution
            )
        except asyncio.TimeoutError:
            # Query took too long - return error without analyzing
            print("⚠️  Query timeout after 30 seconds")
            
            # Don't force refresh schema - just return timeout error
            try:
                # Try to get cached schema quickly (1 second timeout)
                schema_info = await asyncio.wait_for(
                    schema_analyzer.get_database_schema(
                        engine, str(connection.id), force_refresh=False
                    ),
                    timeout=1.0
                )
                available_tables = list(schema_info.get("tables", {}).keys()) if schema_info else []
                
                # Use field analyzer to suggest correct table names
                table_suggestions = []
                if available_tables:
                    from ..services.field_analyzer_service import FieldAnalyzerService
                    field_analyzer = FieldAnalyzerService()
                    
                    # Check if user query contains table name issues
                    query_words = request.prompt.lower().split()
                    for word in query_words:
                        resolved_table = field_analyzer.resolve_table_name(word, available_tables)
                        if resolved_table and resolved_table != word:
                            table_suggestions.append(f"'{word}' should be '{resolved_table}'")
                
                error_message = f"Query timeout after 10 seconds. Likely table name issue.\n"
                if table_suggestions:
                    error_message += f"Suggestions: {', '.join(table_suggestions)}\n"
                if available_tables:
                    error_message += f"Available tables: {', '.join(available_tables[:10])}"
                else:
                    error_message += "Could not retrieve database schema. Check connection."
                    
            except Exception as schema_error:
                error_message = f"Query timeout after 10 seconds and schema analysis failed: {str(schema_error)}"
            
            return QueryResponse(
                prompt=request.prompt,
                generated_sql=None,
                result_type=ResultType.ERROR,
                result_data={
                    "error": error_message,
                    "timeout": True,
                    "analysis_attempted": True
                },
                execution_time=10000  # 10 seconds
            )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create response with retry information
        response_data = result["result_data"]
        if retry_log:
            # Add retry information to response for debugging
            if isinstance(response_data, dict):
                response_data["retry_info"] = {
                    "attempts": len(retry_log) + 1,
                    "retry_log": retry_log
                }
            else:
                # For simple responses, create a dict structure
                response_data = {
                    "result": response_data,
                    "retry_info": {
                        "attempts": len(retry_log) + 1,
                        "retry_log": retry_log
                    }
                }
        
        response = QueryResponse(
            prompt=request.prompt,
            generated_sql=result["sql_query"],
            result_type=result["result_type"],
            result_data=response_data,
            execution_time=execution_time
        )
        
        # Save to history
        history = QueryHistory(
            connection_id=request.connection_id,
            prompt=request.prompt,
            generated_sql=response.generated_sql,
            result_type=response.result_type,
            result_data=safe_json_dumps(response.result_data) if isinstance(response.result_data, (dict, list)) else str(response.result_data),
            execution_time=response.execution_time
        )
        db.add(history)
        await db.commit()
        
        return response
        
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        
        # Check if error has table suggestions attached
        error_data = {"error": str(e)}
        if hasattr(e, 'table_suggestions') and e.table_suggestions:
            error_data.update(e.table_suggestions)
        
        return QueryResponse(
            prompt=request.prompt,
            generated_sql=captured_sql_query,  # Include the SQL that failed
            result_type=ResultType.ERROR,
            result_data=error_data,
            execution_time=execution_time
        )


@router.get("/field-analysis/{connection_id}")
async def get_field_analysis(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get semantic field analysis for a database connection"""
    
    # Get connection
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    if not connection.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection is not active"
        )
    
    try:
        # Get schema with field analysis
        engine = schema_analyzer.create_engine(connection.connection_string)
        schema_info = await schema_analyzer.get_database_schema(
            engine, str(connection_id), force_refresh=False
        )
        
        # Return field analysis if available
        if "field_analysis" in schema_info:
            return schema_info["field_analysis"]
        else:
            return {"error": "Field analysis not available"}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting field analysis: {str(e)}"
        )

@router.get("/field-analysis/{connection_id}/test")
async def get_field_analysis_test(connection_id: int):
    """Get mock field analysis data for testing purposes"""
    return {
        "field_categories": {
            "identity": [
                {"table": "students", "field": "student_id"},
                {"table": "students", "field": "zip_code"},
                {"table": "courses", "field": "course_id"}
            ],
            "personal_info": [
                {"table": "students", "field": "first_name"},
                {"table": "students", "field": "last_name"},
                {"table": "faculty", "field": "first_name"}
            ],
            "contact": [
                {"table": "students", "field": "email"},
                {"table": "students", "field": "phone"},
                {"table": "students", "field": "address"}
            ],
            "temporal": [
                {"table": "students", "field": "birth_date"},
                {"table": "students", "field": "enrollment_date"},
                {"table": "students", "field": "graduation_date"}
            ],
            "academic": [
                {"table": "students", "field": "gpa"},
                {"table": "courses", "field": "course_code"},
                {"table": "enrollments", "field": "grade"}
            ]
        },
        "data_availability": {
            "entities": {
                "student": {"table": "students", "count": 150},
                "course": {"table": "courses", "count": 45},
                "teacher": {"table": "faculty", "count": 25},
                "vehicle": {"table": "vehicles", "count": 85}
            }
        },
        "query_suggestions": [
            {
                "type": "basic",
                "category": "student",
                "query_description": "List all students with their contact information",
                "example_query": "Show me all students with their name, email and phone",
                "confidence": 0.95
            },
            {
                "type": "relationship",
                "category": "academic",
                "query_description": "Find students who own vehicles",
                "example_query": "Which students own cars or vehicles?",
                "confidence": 0.88
            },
            {
                "type": "analysis",
                "category": "academic",
                "query_description": "Students by GPA range",
                "example_query": "Show me students with GPA higher than 3.5",
                "confidence": 0.92
            }
        ],
        "missing_fields": {
            "students": [
                {
                    "field_name": "direct_vehicle_ownership",
                    "reason": "Vehicle ownership must be determined through relationships",
                    "alternatives": ["vehicles.owner_id", "JOIN with vehicles table"]
                }
            ]
        },
        "relationships": [
            {
                "from_table": "enrollments",
                "from_column": "student_id",
                "to_table": "students",
                "to_column": "student_id",
                "relationship_type": "many_to_one"
            },
            {
                "from_table": "vehicles",
                "from_column": "owner_id", 
                "to_table": "students",
                "to_column": "student_id",
                "relationship_type": "many_to_one"
            }
        ],
        "tables": {
            "students": 16,
            "courses": 8,
            "enrollments": 9,
            "faculty": 14,
            "vehicles": 10
        }
    }

@router.get("/schema/{connection_id}")
async def get_database_schema(
    connection_id: int,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get database schema information for a connection"""
    
    # Get connection
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    if not connection.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection is not active"
        )
    
    try:
        # Get database schema information using schema analyzer
        # This handles all database types (SQLite, MSSQL, PostgreSQL, etc.)
        engine = schema_analyzer.create_engine(connection.connection_string)
        
        # Get schema info with caching
        schema_info = await schema_analyzer.get_database_schema(
            engine, 
            str(connection.id),
            force_refresh=force_refresh
        )
        
        # Simplify the response for frontend
        simplified_schema = {
            "tables": [],
            "statistics": schema_info.get("statistics", {}),
            "analyzed_at": schema_info.get("analyzed_at")
        }
        
        for table_name, table_info in schema_info.get("tables", {}).items():
            simplified_table = {
                "name": table_name,
                "type": table_info.get("type", "TABLE"),
                "row_count": table_info.get("row_count", 0),
                "columns": [
                    {
                        "name": col["name"],
                        "type": col["data_type"],
                        "nullable": col["nullable"]
                    }
                    for col in table_info.get("columns", [])
                ],
                "primary_keys": table_info.get("primary_keys", []),
                "foreign_keys": [
                    f"{fk['column']} -> {fk['referenced_table']}.{fk['referenced_column']}"
                    for fk in table_info.get("foreign_keys", [])
                ]
            }
            simplified_schema["tables"].append(simplified_table)
        
        return simplified_schema
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schema: {str(e)}"
        )


@router.get("/history/{connection_id}")
async def get_query_history(
    connection_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get query history for a connection"""
    result = await db.execute(
        select(QueryHistory)
        .where(QueryHistory.connection_id == connection_id)
        .order_by(QueryHistory.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    return history

@router.get("/models")
async def get_available_models():
    """Get available LLM models"""
    return await rag_service.get_available_models()

@router.get("/history/{connection_id}")
async def get_query_history(
    connection_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get query history for a connection"""
    result = await db.execute(
        select(QueryHistory)
        .where(QueryHistory.connection_id == connection_id)
        .order_by(QueryHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    history = result.scalars().all()
    
    # Parse JSON strings back to objects
    history_list = []
    for h in history:
        history_dict = {
            "id": h.id,
            "prompt": h.prompt,
            "generated_sql": h.generated_sql,
            "result_type": h.result_type,
            "result_data": json.loads(h.result_data) if h.result_data else None,
            "execution_time": h.execution_time,
            "created_at": h.created_at.isoformat() if h.created_at else None
        }
        history_list.append(history_dict)
    
    return history_list

@router.get("/enums")
async def get_query_enums():
    """Get all available enums for the frontend"""
    return {
        "result_types": [e.value for e in ResultType],
        "query_types": [e.value for e in QueryType],
        "table_types": [e.value for e in TableType],
        "data_type_categories": [e.value for e in DataTypeCategory]
    }

@router.get("/suggestions/{connection_id}")
async def get_query_suggestions(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get query suggestions based on database schema"""
    
    # Get connection
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    if not connection.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection is not active"
        )
    
    try:
        # Get database schema
        from sqlalchemy import create_engine
        params = MSSQLService.parse_connection_string(connection.connection_string)
        server = params.get('server', 'localhost')
        database = params.get('database', 'master')
        username = params.get('user id') or params.get('uid')
        password = params.get('password') or params.get('pwd')
        
        engine_url = f"mssql+pymssql://{username}:{password}@{server}/{database}"
        engine = create_engine(engine_url)
        
        schema_info = await schema_analyzer.get_database_schema(
            engine, 
            str(connection.id),
            force_refresh=False
        )
        
        # Build suggestions
        tables = list(schema_info.get("tables", {}).keys())
        
        # Find numeric and filterable columns
        aggregation_columns = {}
        filter_columns = {}
        
        for table_name, table_info in schema_info.get("tables", {}).items():
            numeric_cols = []
            filterable_cols = []
            
            for col in table_info.get("columns", []):
                col_type = col["data_type"].lower()
                
                # Numeric columns for aggregation
                if any(t in col_type for t in ["int", "decimal", "float", "numeric", "money"]):
                    numeric_cols.append(col["name"])
                
                # Filterable columns (not binary/large text)
                if not any(t in col_type for t in ["image", "binary", "varbinary", "text", "ntext"]):
                    filterable_cols.append(col["name"])
            
            if numeric_cols:
                aggregation_columns[table_name] = numeric_cols
            if filterable_cols:
                filter_columns[table_name] = filterable_cols
        
        # Create common query templates
        common_queries = []
        
        if tables:
            # Basic templates for the first table (or most important one)
            main_table = tables[0] if tables else "table_name"
            
            common_queries.extend([
                QueryTemplate(
                    name="Count All Records",
                    description=f"Count total records in a table",
                    query_type=QueryType.COUNT,
                    template=f"SELECT COUNT(*) FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Select Top Records",
                    description="Get first N records from a table",
                    query_type=QueryType.SELECT,
                    template=f"SELECT TOP 10 * FROM {main_table}",
                    parameters=[]
                ),
                QueryTemplate(
                    name="Search by Value",
                    description="Find records containing specific value",
                    query_type=QueryType.SELECT,
                    template=f"SELECT * FROM {main_table} WHERE column_name LIKE '%value%'",
                    parameters=["column_name", "value"]
                ),
            ])
            
            # Add aggregation templates if numeric columns exist
            if aggregation_columns.get(main_table):
                numeric_col = aggregation_columns[main_table][0]
                common_queries.extend([
                    QueryTemplate(
                        name="Calculate Average",
                        description="Calculate average of numeric column",
                        query_type=QueryType.AGGREGATE,
                        template=f"SELECT AVG({numeric_col}) FROM {main_table}",
                        parameters=[]
                    ),
                    QueryTemplate(
                        name="Calculate Sum",
                        description="Calculate sum of numeric column",
                        query_type=QueryType.AGGREGATE,
                        template=f"SELECT SUM({numeric_col}) FROM {main_table}",
                        parameters=[]
                    ),
                    QueryTemplate(
                        name="Find Maximum",
                        description="Find maximum value in column",
                        query_type=QueryType.AGGREGATE,
                        template=f"SELECT MAX({numeric_col}) FROM {main_table}",
                        parameters=[]
                    ),
                ])
        
        suggestions = QuerySuggestions(
            tables=tables,
            common_queries=common_queries,
            aggregation_columns=aggregation_columns,
            filter_columns=filter_columns
        )
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )

def categorize_data_type(data_type: str) -> DataTypeCategory:
    """Categorize SQL data types into categories"""
    data_type_lower = data_type.lower()
    
    if any(t in data_type_lower for t in ["int", "decimal", "float", "numeric", "money", "real", "smallmoney"]):
        return DataTypeCategory.NUMERIC
    elif any(t in data_type_lower for t in ["char", "varchar", "text", "nchar", "nvarchar", "ntext"]):
        return DataTypeCategory.TEXT
    elif any(t in data_type_lower for t in ["date", "time", "datetime", "timestamp"]):
        return DataTypeCategory.DATE
    elif any(t in data_type_lower for t in ["bit", "bool"]):
        return DataTypeCategory.BOOLEAN
    elif any(t in data_type_lower for t in ["binary", "varbinary", "image"]):
        return DataTypeCategory.BINARY
    elif any(t in data_type_lower for t in ["json", "xml"]):
        return DataTypeCategory.JSON
    else:
        return DataTypeCategory.OTHER

from pydantic import BaseModel

class LoadEnumsRequest(BaseModel):
    file_path: str

@router.post("/enums/{connection_id}/load")
async def load_enums_for_connection(
    connection_id: int,
    request: LoadEnumsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Load enums from JSON file for a specific connection"""
    
    # Verify connection exists
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Load enums
    success = await enum_service.load_enums_from_file(request.file_path, str(connection_id))
    
    if success:
        return {"message": "Enums loaded successfully", "connection_id": connection_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to load enums from file"
        )

@router.get("/enums/{connection_id}/suggestions")
async def get_enum_suggestions(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get enum suggestions for a specific connection"""
    
    # Verify connection exists
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    suggestions = enum_service.get_enum_suggestions(str(connection_id))
    return suggestions

@router.get("/enums/{connection_id}/explain/{enum_name}")
async def explain_enum(
    connection_id: int,
    enum_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Explain how to use a specific enum in queries"""
    
    # Verify connection exists
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    explanation = enum_service.explain_enum_usage(enum_name, str(connection_id))
    return {"enum_name": enum_name, "explanation": explanation}

@router.post("/enums/{connection_id}/upload")
async def upload_enum_file(
    connection_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload an enum JSON file for a connection"""
    
    # Verify connection exists
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are allowed"
        )
    
    # Read and validate JSON content
    content = await file.read()
    try:
        json_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    
    # Generate unique filename
    unique_filename = f"{connection_id}_{uuid.uuid4().hex}_{file.filename}"
    file_path = Path("/home/rick/source/dbairag/backend/enum_files") / unique_filename
    
    # Save file to disk
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Save to database
    enum_file = EnumFile(
        connection_id=connection_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        content_json=json.dumps(json_data),
        description=description,
        is_active=True
    )
    
    db.add(enum_file)
    await db.commit()
    await db.refresh(enum_file)
    
    # Reload enums in service
    from ..services.enum_service import enum_service
    await enum_service.load_enums_from_database(db, connection_id)
    
    return {
        "id": enum_file.id,
        "filename": enum_file.original_filename,
        "description": enum_file.description,
        "created_at": enum_file.created_at
    }

@router.get("/enums/{connection_id}/files")
async def list_enum_files(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all enum files for a connection"""
    
    # Verify connection exists
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Get enum files
    result = await db.execute(
        select(EnumFile).where(
            EnumFile.connection_id == connection_id,
            EnumFile.is_active == True
        )
    )
    enum_files = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "filename": f.original_filename,
            "description": f.description,
            "created_at": f.created_at,
            "updated_at": f.updated_at
        }
        for f in enum_files
    ]

@router.delete("/enums/{connection_id}/files/{file_id}")
async def delete_enum_file(
    connection_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an enum file"""
    
    # Get enum file
    result = await db.execute(
        select(EnumFile).where(
            EnumFile.id == file_id,
            EnumFile.connection_id == connection_id
        )
    )
    enum_file = result.scalar_one_or_none()
    
    if not enum_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enum file not found"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(enum_file.file_path):
            os.remove(enum_file.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete from database
    await db.delete(enum_file)
    await db.commit()
    
    # Reload enums in service
    from ..services.enum_service import enum_service
    await enum_service.load_enums_from_database(db, connection_id)
    
    # Invalidate cache for this connection
    if redis_service.is_connected:
        await redis_service.invalidate_connection_cache(str(connection_id))
    
    return {"message": "Enum file deleted successfully"}

@router.post("/cache/invalidate/{connection_id}")
async def invalidate_cache(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Invalidate all cache entries for a connection"""
    
    # Verify connection exists
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    if not redis_service.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis cache not available"
        )
    
    deleted_count = await redis_service.invalidate_connection_cache(str(connection_id))
    
    return {
        "message": f"Cache invalidated for connection {connection_id}",
        "deleted_entries": deleted_count
    }

@router.get("/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    
    if not redis_service.is_connected:
        return {
            "connected": False,
            "message": "Redis cache not available"
        }
    
    stats = await redis_service.get_cache_stats()
    return stats

@router.get("/documentation/{connection_id}")
async def get_database_documentation(
    connection_id: int,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive database documentation with relationships and field descriptions"""
    
    # Get connection
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Check cache first
    cache_key = f"documentation:{connection_id}"
    if redis_service.is_connected:
        cached_doc = await redis_service.get(cache_key, prefix="docs")
        if cached_doc:
            if format == "markdown":
                return {
                    "format": "markdown",
                    "content": documentation_service.generate_markdown_documentation(cached_doc)
                }
            return cached_doc
    
    # Generate documentation
    documentation = await documentation_service.get_database_documentation(connection.connection_string)
    
    if 'error' in documentation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate documentation: {documentation['error']}"
        )
    
    # Cache the documentation
    if redis_service.is_connected:
        await redis_service.set(
            cache_key,
            documentation,
            prefix="docs",
            ttl=7200  # Cache for 2 hours
        )
    
    # Return based on format
    if format == "markdown":
        return {
            "format": "markdown",
            "content": documentation_service.generate_markdown_documentation(documentation)
        }
    
    return documentation

@router.post("/documentation/{connection_id}/refresh")
async def refresh_documentation(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Refresh database documentation (clear cache and regenerate)"""
    
    # Clear cache
    cache_key = f"documentation:{connection_id}"
    if redis_service.is_connected:
        await redis_service.delete(f"docs:{cache_key}")
    
    # Regenerate documentation
    return await get_database_documentation(connection_id, "json", db)

@router.get("/schema/sync-status/{connection_id}")
async def get_schema_sync_status(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the schema sync status for a connection"""
    from ..models import SchemaSyncStatus, CachedSchema
    
    # Get sync status
    result = await db.execute(
        select(SchemaSyncStatus).where(SchemaSyncStatus.connection_id == connection_id)
    )
    sync_status = result.scalar_one_or_none()
    
    # Count cached tables
    result = await db.execute(
        select(CachedSchema).where(CachedSchema.connection_id == connection_id)
    )
    cached_tables = result.scalars().all()
    
    if not sync_status:
        return {
            "connection_id": connection_id,
            "sync_status": "never_synced",
            "cached_tables": 0,
            "message": "Schema has never been synced for this connection"
        }
    
    return {
        "connection_id": connection_id,
        "sync_status": sync_status.sync_status,
        "last_sync_started": sync_status.last_sync_started.isoformat() if sync_status.last_sync_started else None,
        "last_sync_completed": sync_status.last_sync_completed.isoformat() if sync_status.last_sync_completed else None,
        "sync_duration_ms": sync_status.sync_duration_ms,
        "tables_synced": sync_status.tables_synced,
        "cached_tables": len(cached_tables),
        "error_message": sync_status.error_message,
        "schema_hash": sync_status.schema_hash
    }

@router.post("/schema/sync/{connection_id}")
async def trigger_schema_sync(
    connection_id: int,
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger schema sync for a connection"""
    
    # Get connection
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    try:
        # Trigger sync with timeout
        schema_info = await asyncio.wait_for(
            schema_sync_service.check_and_sync_schema(
                connection_id=connection.id,
                connection_string=connection.connection_string,
                db_session=db,
                force_refresh=force_refresh
            ),
            timeout=15.0  # 15 second timeout
        )
        
        return {
            "success": True,
            "message": "Schema sync completed successfully",
            "tables_synced": len(schema_info.get("tables", {})) if schema_info else 0,
            "sync_metadata": schema_info.get("sync_metadata") if schema_info else None
        }
        
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": "Schema sync timeout after 30 seconds",
            "error": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Schema sync failed: {str(e)}",
            "error": str(e)
        }

@router.get("/schema/sync-stats")
async def get_sync_statistics(db: AsyncSession = Depends(get_db)):
    """Get overall schema sync statistics"""
    stats = await schema_sync_service.get_sync_statistics(db)
    return stats

@router.get("/performance/metrics")
async def get_performance_metrics():
    """Get detailed performance metrics from optimized RAG service"""
    return {
        "optimized_rag_metrics": optimized_rag_service.get_performance_summary(),
        "schema_cache_stats": await schema_cache_service.get_cache_stats(),
        "timestamp": time.time()
    }

@router.post("/schema/refresh/{connection_id}")
async def refresh_schema_cache(connection_id: int, db: AsyncSession = Depends(get_db)):
    """Force refresh schema cache for a connection"""
    try:
        # Get connection
        result = await db.execute(
            select(ConnectionModel).where(ConnectionModel.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        # Invalidate cache first
        await schema_cache_service.invalidate_cache(str(connection_id))
        
        # Force refresh
        start_time = time.time()
        schema_info = await schema_cache_service.get_cached_schema(
            str(connection_id), connection.connection_string, force_refresh=True
        )
        refresh_time = time.time() - start_time
        
        return {
            "connection_id": connection_id,
            "connection_name": connection.name,
            "refresh_time_ms": int(refresh_time * 1000),
            "tables_found": len(schema_info.get("tables", {})),
            "total_columns": sum(len(t.get("columns", [])) for t in schema_info.get("tables", {}).values()),
            "cache_updated": True
        }
        
    except Exception as e:
        logger.error(f"❌ Schema refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema refresh failed: {str(e)}"
        )

@router.get("/schema/stats")
async def get_schema_cache_stats():
    """Get schema cache performance statistics"""
    try:
        stats = await schema_cache_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"❌ Schema stats error: {str(e)}")
        return {
            "error": str(e),
            "timestamp": time.time()
        }
