"""
Queries service for handling comprehensive context and query execution
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def get_comprehensive_context(
    schema_analyzer,
    enum_service, 
    documentation_service,
    connection,
    connection_id: str,
    db: AsyncSession,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Get comprehensive database context including schema, enums, and documentation
    
    Args:
        schema_analyzer: Schema analysis service
        enum_service: Enum management service
        documentation_service: Documentation service
        connection: Database connection object
        connection_id: Connection identifier
        db: Database session
        force_refresh: Whether to force refresh all metadata
        
    Returns:
        Dict containing comprehensive database context
    """
    try:
        logger.info(f"Getting comprehensive context for connection {connection_id}")
        
        # Get database schema information
        engine = schema_analyzer.create_engine(connection.connection_string)
        schema_info = await schema_analyzer.get_database_schema(
            engine, 
            connection_id,
            force_refresh=force_refresh
        )
        
        # Load and get enum information
        if force_refresh:
            await enum_service.load_enums_from_database(db, int(connection_id))
        
        enums = enum_service.get_enum_suggestions(connection_id)
        
        # Get documentation with relationships
        documentation = await documentation_service.get_database_documentation(
            connection.connection_string,
            force_refresh=force_refresh
        )
        
        # Prepare comprehensive context
        comprehensive_context = {
            "schema_info": schema_info,
            "enums": enums,
            "documentation": documentation if 'error' not in documentation else None,
            "connection_id": connection_id,
            "context_type": "comprehensive",
            "force_refreshed": force_refresh
        }
        
        logger.info(f"Comprehensive context prepared for connection {connection_id}")
        return comprehensive_context
        
    except Exception as e:
        logger.error(f"Error getting comprehensive context for connection {connection_id}: {e}")
        raise

async def execute_query_with_context(
    rag_service,
    prompt: str,
    comprehensive_context: Dict[str, Any],
    connection_id: Optional[str] = None
) -> tuple:
    """
    Execute RAG query with comprehensive context
    
    Args:
        rag_service: RAG service for SQL generation
        prompt: User prompt for SQL generation
        comprehensive_context: Database context information
        connection_id: Connection identifier
        
    Returns:
        Tuple of (generated_sql, result_data)
    """
    try:
        logger.info(f"Executing query with comprehensive context for connection {connection_id}")
        
        # Generate SQL with comprehensive context
        generated_sql, result_data = await rag_service.generate_sql_with_full_context(
            prompt, comprehensive_context, connection_id
        )
        
        logger.info(f"Query executed successfully for connection {connection_id}")
        return generated_sql, result_data
        
    except Exception as e:
        logger.error(f"Error executing query for connection {connection_id}: {e}")
        raise

async def refresh_all_metadata(
    schema_analyzer,
    enum_service,
    documentation_service, 
    connection,
    connection_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Refresh all database metadata (schema, enums, documentation)
    
    Args:
        schema_analyzer: Schema analysis service
        enum_service: Enum management service
        documentation_service: Documentation service
        connection: Database connection object
        connection_id: Connection identifier
        db: Database session
        
    Returns:
        Dict with refresh results and statistics
    """
    try:
        logger.info(f"Starting comprehensive metadata refresh for connection {connection_id}")
        refresh_results = {
            "connection_id": connection_id,
            "refreshed_components": [],
            "errors": []
        }
        
        # Refresh schema information
        try:
            engine = schema_analyzer.create_engine(connection.connection_string)
            schema_info = await schema_analyzer.get_database_schema(
                engine,
                connection_id, 
                force_refresh=True
            )
            refresh_results["refreshed_components"].append("schema")
            refresh_results["schema_tables"] = len(schema_info.get("tables", {}))
            logger.info(f"Schema refreshed: {refresh_results['schema_tables']} tables")
        except Exception as e:
            error_msg = f"Schema refresh failed: {str(e)}"
            refresh_results["errors"].append(error_msg)
            logger.error(error_msg)
        
        # Refresh enum information
        try:
            await enum_service.load_enums_from_database(db, int(connection_id))
            enums = enum_service.get_enum_suggestions(connection_id)
            refresh_results["refreshed_components"].append("enums")
            refresh_results["enum_types"] = len(enums) if isinstance(enums, dict) else 0
            logger.info(f"Enums refreshed: {refresh_results['enum_types']} types")
        except Exception as e:
            error_msg = f"Enum refresh failed: {str(e)}"
            refresh_results["errors"].append(error_msg)
            logger.error(error_msg)
        
        # Refresh documentation
        try:
            documentation = await documentation_service.get_database_documentation(
                connection.connection_string,
                force_refresh=True
            )
            refresh_results["refreshed_components"].append("documentation")
            
            # Count documentation elements
            if isinstance(documentation, dict) and 'error' not in documentation:
                refresh_results["documented_tables"] = len(documentation.get("tables", {}))
                refresh_results["relationships"] = len(documentation.get("relationships", []))
            logger.info("Documentation refreshed successfully")
        except Exception as e:
            error_msg = f"Documentation refresh failed: {str(e)}"
            refresh_results["errors"].append(error_msg)
            logger.error(error_msg)
        
        refresh_results["success"] = len(refresh_results["errors"]) == 0
        refresh_results["partial_success"] = len(refresh_results["refreshed_components"]) > 0
        
        logger.info(f"Metadata refresh completed for connection {connection_id}. "
                   f"Components refreshed: {refresh_results['refreshed_components']}")
        
        return refresh_results
        
    except Exception as e:
        logger.error(f"Critical error in metadata refresh for connection {connection_id}: {e}")
        raise