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
from ..database import get_db
from ..models import Connection as ConnectionModel, QueryHistory, EnumFile
from ..schemas import (
    QueryRequest, QueryResponse, ResultType, QueryType,
    TableType, DataTypeCategory, QueryTemplate, QuerySuggestions,
    DatabaseSchema, TableInfo, ColumnInfo
)
from ..services import MSSQLService
from ..services.rag_service import RAGService
from ..services.schema_analyzer import SchemaAnalyzer
from ..services.enum_service import enum_service
from ..services.redis_service import redis_service
from ..services.documentation_service import documentation_service
from ..utils.json_utils import safe_json_dumps

router = APIRouter(prefix="/api/queries", tags=["queries"])

rag_service = RAGService()
schema_analyzer = SchemaAnalyzer()

# Initialize Redis service for all services
schema_analyzer.set_redis_service(redis_service)
enum_service.set_redis_service(redis_service)
rag_service.set_redis_service(redis_service)

@router.post("/execute", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a natural language query against a database"""
    
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
            sql_query, metadata = await rag_service.generate_sql(request.prompt, None, "1")
            
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
        # FORCE REFRESH: Read all database metadata before SQL generation
        from sqlalchemy import create_engine
        # Parse connection string to SQLAlchemy format
        params = MSSQLService.parse_connection_string(connection.connection_string)
        server = params.get('server', 'localhost')
        database = params.get('database', 'master')
        username = params.get('user id') or params.get('uid')
        password = params.get('password') or params.get('pwd')
        
        # Create SQLAlchemy engine
        engine_url = f"mssql+pymssql://{username}:{password}@{server}/{database}"
        engine = create_engine(engine_url)
        
        # FORCE REFRESH: Always get fresh schema information
        schema_info = await schema_analyzer.get_database_schema(
            engine, 
            str(connection.id),
            force_refresh=True  # Always refresh to get latest metadata
        )
        
        # FORCE REFRESH: Reload enums from database
        await enum_service.load_enums_from_database(db, connection.id)
        
        # FORCE REFRESH: Get fresh documentation with relationships
        documentation = await documentation_service.get_database_documentation(connection.connection_string)
        
        # Combine all metadata for comprehensive context
        comprehensive_context = {
            "schema_info": schema_info,
            "enums": enum_service.get_enum_suggestions(str(connection.id)),
            "documentation": documentation if 'error' not in documentation else None,
            "connection_id": str(connection.id)
        }
        
        # Generate SQL from prompt using RAG with FULL context (schema + enums + docs)
        sql_query, metadata = await rag_service.generate_sql_with_full_context(
            request.prompt, 
            comprehensive_context, 
            str(connection.id)
        )
        
        # If we have enum translations, apply them
        if sql_query and connection.id:
            sql_query = enum_service.translate_enum_in_query(sql_query, str(connection.id))
        
        if not sql_query:
            error_msg = metadata.get("error", "Failed to generate SQL")
            response = QueryResponse(
                prompt=request.prompt,
                generated_sql=None,
                result_type=ResultType.ERROR,
                result_data={"error": error_msg},
                execution_time=int((time.time() - start_time) * 1000)
            )
        else:
            # Execute the SQL query
            df, error = await MSSQLService.execute_query_async(
                connection.connection_string,
                sql_query
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            if error:
                response = QueryResponse(
                    prompt=request.prompt,
                    generated_sql=sql_query,
                    result_type=ResultType.ERROR,
                    result_data={"error": error},
                    execution_time=execution_time
                )
            else:
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
                    result_data = error if error else "Query executed successfully"
                    result_type = ResultType.TEXT
                
                response = QueryResponse(
                    prompt=request.prompt,
                    generated_sql=sql_query,
                    result_type=result_type,
                    result_data=result_data,
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
        return QueryResponse(
            prompt=request.prompt,
            generated_sql=None,
            result_type=ResultType.ERROR,
            result_data={"error": str(e)},
            execution_time=execution_time
        )


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
        # Get database schema information
        from sqlalchemy import create_engine
        # Parse connection string to SQLAlchemy format
        params = MSSQLService.parse_connection_string(connection.connection_string)
        server = params.get('server', 'localhost')
        database = params.get('database', 'master')
        username = params.get('user id') or params.get('uid')
        password = params.get('password') or params.get('pwd')
        
        # Create SQLAlchemy engine
        engine_url = f"mssql+pymssql://{username}:{password}@{server}/{database}"
        engine = create_engine(engine_url)
        
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
