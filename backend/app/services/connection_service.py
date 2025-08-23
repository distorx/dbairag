"""
Generic connection testing service that supports multiple database types
"""
import asyncio
from typing import Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
import logging

logger = logging.getLogger(__name__)

class ConnectionService:
    @staticmethod
    async def test_connection_async(connection_string: str, database_type: str = "mssql") -> Tuple[bool, str]:
        """
        Test database connection based on database type
        
        Args:
            connection_string: Database connection string
            database_type: Type of database (mssql, sqlite, postgresql, etc.)
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if database_type == "sqlite":
                # SQLite connections are synchronous
                engine = create_engine(connection_string)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                engine.dispose()
                return True, "Connection successful"
                
            elif database_type in ["mssql", "postgresql", "mysql"]:
                # Use pymssql for MSSQL
                if database_type == "mssql":
                    from ..services.mssql_service import MSSQLService
                    return await MSSQLService.test_connection_async(connection_string)
                else:
                    # For other async databases
                    engine = create_async_engine(connection_string)
                    async with engine.connect() as conn:
                        await conn.execute(text("SELECT 1"))
                    await engine.dispose()
                    return True, "Connection successful"
            else:
                return False, f"Unsupported database type: {database_type}"
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False, str(e)