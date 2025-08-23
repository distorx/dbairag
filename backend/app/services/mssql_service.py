import pymssql
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)

class MSSQLService:
    @staticmethod
    def parse_connection_string(connection_string: str) -> Dict[str, str]:
        """Parse MSSQL connection string"""
        params = {}
        parts = connection_string.split(';')
        
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['server', 'data source']:
                    params['server'] = value
                elif key in ['database', 'initial catalog']:
                    params['database'] = value
                elif key in ['user id', 'uid', 'user']:
                    params['user'] = value
                elif key in ['password', 'pwd']:
                    params['password'] = value
                elif key == 'trusted_connection' and value.lower() in ['true', 'yes']:
                    params['trusted_connection'] = True
        
        return params
    
    @staticmethod
    def execute_query(connection_string: str, query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Execute SQL query and return results"""
        try:
            params = MSSQLService.parse_connection_string(connection_string)
            
            # Connect to MSSQL
            with pymssql.connect(**params) as conn:
                # Use pandas to read SQL query
                if query.strip().upper().startswith(('SELECT', 'WITH', 'SHOW', 'DESCRIBE')):
                    df = pd.read_sql(query, conn)
                    return df, None
                else:
                    # For non-SELECT queries
                    with conn.cursor() as cursor:
                        cursor.execute(query)
                        conn.commit()
                        rows_affected = cursor.rowcount
                        return None, f"Query executed successfully. Rows affected: {rows_affected}"
        
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    async def execute_query_async(connection_string: str, query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Execute query asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            MSSQLService.execute_query,
            connection_string,
            query
        )
    
    @staticmethod
    def test_connection(connection_string: str) -> Tuple[bool, str]:
        """Test MSSQL connection"""
        try:
            params = MSSQLService.parse_connection_string(connection_string)
            with pymssql.connect(**params) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    async def test_connection_async(connection_string: str) -> Tuple[bool, str]:
        """Test connection asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            MSSQLService.test_connection,
            connection_string
        )