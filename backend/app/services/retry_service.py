import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
import time
import re
from sqlalchemy.exc import SQLAlchemyError
from pymssql import Error as PyMSSQLError
from .table_suggestion_service import TableSuggestionService

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Classification of database errors for retry logic"""
    SCHEMA_ERROR = "schema_error"  # Table/column doesn't exist
    PERMISSION_ERROR = "permission_error"  # Access denied
    CONNECTION_ERROR = "connection_error"  # Network/connection issues  
    TIMEOUT_ERROR = "timeout_error"  # Query timeout
    SYNTAX_ERROR = "syntax_error"  # SQL syntax issues
    CONSTRAINT_ERROR = "constraint_error"  # FK/PK violations
    UNKNOWN_ERROR = "unknown_error"  # Other errors

class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 30.0  # seconds
        self.backoff_factor = 2.0
        self.refresh_metadata_on_schema_error = True
        self.refresh_metadata_on_unknown_error = True

class RetryService:
    """
    Intelligent retry service for SQL queries with automatic database metadata refresh
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.table_suggestion_service = TableSuggestionService()
        self.schema_error_patterns = [
            r"invalid object name",
            r"invalid column name", 
            r"column .* doesn't exist",
            r"table .* doesn't exist",
            r"unknown column",
            r"no such table",
            r"relation .* does not exist"
        ]
        self.connection_error_patterns = [
            r"connection.*lost",
            r"server.*gone away",
            r"connection.*closed",
            r"network.*error",
            r"timeout",
            r"communication link failure"
        ]
        self.permission_error_patterns = [
            r"access denied",
            r"permission denied",
            r"insufficient privileges",
            r"not authorized"
        ]
    
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify database error to determine retry strategy"""
        error_msg = str(error).lower()
        
        # Check for schema-related errors
        for pattern in self.schema_error_patterns:
            if re.search(pattern, error_msg):
                return ErrorType.SCHEMA_ERROR
                
        # Check for connection errors
        for pattern in self.connection_error_patterns:
            if re.search(pattern, error_msg):
                return ErrorType.CONNECTION_ERROR
                
        # Check for permission errors
        for pattern in self.permission_error_patterns:
            if re.search(pattern, error_msg):
                return ErrorType.PERMISSION_ERROR
        
        # Check for specific SQL error types
        if "timeout" in error_msg:
            return ErrorType.TIMEOUT_ERROR
        elif "syntax" in error_msg or "parse" in error_msg:
            return ErrorType.SYNTAX_ERROR
        elif "foreign key" in error_msg or "constraint" in error_msg:
            return ErrorType.CONSTRAINT_ERROR
            
        return ErrorType.UNKNOWN_ERROR
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if we should retry based on error type and attempt count"""
        if attempt >= self.config.max_retries:
            return False
            
        # Don't retry permission or syntax errors - they won't fix themselves
        if error_type in [ErrorType.PERMISSION_ERROR, ErrorType.SYNTAX_ERROR]:
            return False
            
        # Retry connection, timeout, schema, and unknown errors
        return error_type in [
            ErrorType.CONNECTION_ERROR, 
            ErrorType.TIMEOUT_ERROR,
            ErrorType.SCHEMA_ERROR,
            ErrorType.UNKNOWN_ERROR
        ]
    
    def should_refresh_metadata(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if we should refresh database metadata before retry"""
        # Always refresh on first schema error
        if error_type == ErrorType.SCHEMA_ERROR and attempt <= 1:
            return self.config.refresh_metadata_on_schema_error
            
        # Refresh on unknown errors (might be schema issues)
        if error_type == ErrorType.UNKNOWN_ERROR and attempt <= 1:
            return self.config.refresh_metadata_on_unknown_error
            
        return False
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff"""
        delay = self.config.base_delay * (self.config.backoff_factor ** attempt)
        return min(delay, self.config.max_delay)
    
    async def execute_with_retry(
        self, 
        query_func,
        refresh_metadata_func,
        context: Dict[str, Any],
        operation_name: str = "query",
        schema_info: Optional[Dict[str, Any]] = None,
        original_sql_query: Optional[str] = None
    ) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Execute a database operation with intelligent retry logic
        
        Args:
            query_func: Async function that executes the query
            refresh_metadata_func: Async function that refreshes database metadata
            context: Context information for logging and error reporting
            operation_name: Name of operation for logging
            schema_info: Database schema information for generating suggestions
            original_sql_query: Original SQL query for suggestion generation
            
        Returns:
            Tuple of (result, retry_log)
        """
        retry_log = []
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                start_time = time.time()
                result = await query_func()
                
                if attempt > 0:
                    retry_log.append({
                        "attempt": attempt + 1,
                        "status": "success",
                        "message": f"{operation_name} succeeded after {attempt} retries",
                        "execution_time_ms": int((time.time() - start_time) * 1000)
                    })
                    logger.info(f"{operation_name} succeeded after {attempt} retries")
                
                return result, retry_log
                
            except Exception as error:
                last_error = error
                error_type = self.classify_error(error)
                
                retry_entry = {
                    "attempt": attempt + 1,
                    "status": "failed",
                    "error_type": error_type.value,
                    "error_message": str(error),
                    "execution_time_ms": int((time.time() - start_time) * 1000)
                }
                
                logger.warning(
                    f"{operation_name} attempt {attempt + 1} failed: {error_type.value} - {error}"
                )
                
                # Check if we should retry
                if not self.should_retry(error_type, attempt):
                    retry_entry["message"] = f"No retry - {error_type.value} not retryable"
                    retry_log.append(retry_entry)
                    break
                
                # Check if we should refresh metadata
                should_refresh = self.should_refresh_metadata(error_type, attempt)
                if should_refresh:
                    try:
                        refresh_start = time.time()
                        await refresh_metadata_func()
                        refresh_time = int((time.time() - refresh_start) * 1000)
                        retry_entry["metadata_refreshed"] = True
                        retry_entry["refresh_time_ms"] = refresh_time
                        logger.info(f"Refreshed database metadata due to {error_type.value}")
                    except Exception as refresh_error:
                        retry_entry["metadata_refresh_failed"] = str(refresh_error)
                        logger.error(f"Failed to refresh metadata: {refresh_error}")
                
                # Calculate delay for next attempt
                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    retry_entry["next_retry_delay_s"] = delay
                    retry_entry["message"] = f"Retrying in {delay}s due to {error_type.value}"
                    retry_log.append(retry_entry)
                    
                    logger.info(f"Retrying {operation_name} in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    retry_entry["message"] = f"Max retries exceeded - {error_type.value}"
                    retry_log.append(retry_entry)
                    break
        
        # If we get here, all retries failed
        logger.error(f"{operation_name} failed after {self.config.max_retries} retries: {last_error}")
        
        # For schema errors, generate table suggestions before raising the error
        if last_error and self.classify_error(last_error) == ErrorType.SCHEMA_ERROR:
            suggestions = await self._generate_table_suggestions(
                last_error, original_sql_query, schema_info
            )
            if suggestions:
                # Attach suggestions to the retry log
                if retry_log:
                    retry_log[-1]["table_suggestions"] = suggestions
                # Create an enhanced error with suggestions
                enhanced_error = Exception(
                    self.table_suggestion_service.generate_enhanced_error_message(
                        str(last_error), suggestions
                    )
                )
                # Copy over the suggestions to the enhanced error for API response
                enhanced_error.table_suggestions = suggestions
                raise enhanced_error
        
        raise last_error

    async def _generate_table_suggestions(
        self, 
        error: Exception, 
        sql_query: Optional[str], 
        schema_info: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate table suggestions for schema errors"""
        try:
            if not sql_query or not schema_info:
                return None
            
            # Extract missing table names from error and query
            missing_tables = self.table_suggestion_service.extract_table_names_from_error(
                str(error), sql_query
            )
            
            if not missing_tables:
                return None
            
            # Get available table names from schema
            available_tables = list(schema_info.get("tables", {}).keys())
            
            if not available_tables:
                return None
            
            # Generate suggestions
            suggestions = self.table_suggestion_service.suggest_tables(
                missing_tables, available_tables
            )
            
            if suggestions:
                # Format for API response with field analysis
                formatted_suggestions = self.table_suggestion_service.format_suggestions_for_response(
                    suggestions, sql_query, schema_info
                )
                logger.info(f"Generated {len(suggestions)} table suggestions for schema error")
                return formatted_suggestions
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating table suggestions: {e}")
            return None

class QueryRetryWrapper:
    """
    Wrapper for query execution with retry logic and metadata refresh
    """
    
    def __init__(self, retry_service: RetryService):
        self.retry_service = retry_service
    
    async def execute_query_with_retry(
        self,
        rag_service,
        schema_analyzer, 
        enum_service,
        documentation_service,
        connection,
        prompt: str,
        connection_id: str
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Execute RAG query with comprehensive retry logic and metadata refresh
        """
        
        async def query_func():
            """Execute the actual query"""
            # Get fresh comprehensive context
            from .queries_service import get_comprehensive_context
            db = None  # We'll need to pass this properly
            
            comprehensive_context = await get_comprehensive_context(
                schema_analyzer, enum_service, documentation_service,
                connection, connection_id, db
            )
            
            # Generate SQL with comprehensive context
            generated_sql, result_data = await rag_service.generate_sql_with_full_context(
                prompt, comprehensive_context, connection_id
            )
            
            return {
                "generated_sql": generated_sql,
                "result_data": result_data,
                "context_used": "comprehensive_with_retry"
            }
        
        async def refresh_metadata_func():
            """Refresh all database metadata"""
            logger.info(f"Refreshing database metadata for connection {connection_id}")
            
            # Force refresh schema
            await schema_analyzer.get_database_schema(
                schema_analyzer.create_engine(connection.connection_string),
                connection_id,
                force_refresh=True
            )
            
            # Force refresh enums
            db = None  # We'll need to pass this properly
            await enum_service.load_enums_from_database(db, int(connection_id))
            
            # Force refresh documentation
            await documentation_service.get_database_documentation(
                connection.connection_string,
                force_refresh=True
            )
            
            logger.info(f"Database metadata refreshed for connection {connection_id}")
        
        return await self.retry_service.execute_with_retry(
            query_func,
            refresh_metadata_func, 
            {"connection_id": connection_id, "prompt": prompt},
            "RAG SQL Query"
        )