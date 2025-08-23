"""
Generic query execution service that supports multiple database types
"""
import pandas as pd
from typing import Tuple, Optional
from sqlalchemy import create_engine, text
import logging

logger = logging.getLogger(__name__)

class QueryExecutionService:
    @staticmethod
    async def execute_query_async(
        connection_string: str, 
        sql_query: str,
        database_type: str = "mssql"
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Execute SQL query based on database type
        
        Args:
            connection_string: Database connection string
            sql_query: SQL query to execute
            database_type: Type of database (mssql, sqlite, postgresql, etc.)
            
        Returns:
            Tuple of (dataframe, error_message)
        """
        try:
            if database_type == "sqlite":
                # SQLite uses synchronous connections
                engine = create_engine(connection_string)
                
                # Remove MSSQL-specific syntax if present
                sql_query = sql_query.replace(" WITH (NOLOCK)", "")
                
                # Execute query
                with engine.connect() as conn:
                    result = conn.execute(text(sql_query))
                    
                    # Check if it's a SELECT query
                    if sql_query.strip().upper().startswith('SELECT'):
                        # Fetch results into DataFrame
                        df = pd.DataFrame(result.fetchall())
                        if not df.empty:
                            df.columns = result.keys()
                        return df, None
                    else:
                        # For non-SELECT queries, return affected rows
                        affected_rows = result.rowcount
                        df = pd.DataFrame([{'affected_rows': affected_rows}])
                        return df, None
                        
            elif database_type == "mssql":
                # Use the existing MSSQL service
                from ..services.mssql_service import MSSQLService
                return await MSSQLService.execute_query_async(connection_string, sql_query)
                
            elif database_type in ["postgresql", "mysql"]:
                # For other databases, use SQLAlchemy
                engine = create_engine(connection_string)
                
                with engine.connect() as conn:
                    result = conn.execute(text(sql_query))
                    
                    if sql_query.strip().upper().startswith('SELECT'):
                        df = pd.DataFrame(result.fetchall())
                        if not df.empty:
                            df.columns = result.keys()
                        return df, None
                    else:
                        affected_rows = result.rowcount
                        df = pd.DataFrame([{'affected_rows': affected_rows}])
                        return df, None
                        
            else:
                return None, f"Unsupported database type: {database_type}"
                
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return None, str(e)