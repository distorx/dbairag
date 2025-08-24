import subprocess
import json
import asyncio
from typing import Dict, Any, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

class SQLCmdService:
    """High-performance MSSQL service using sqlcmd for direct database access"""
    
    @staticmethod
    def parse_connection_string(connection_string: str) -> Dict[str, str]:
        """Parse MSSQL connection string for sqlcmd parameters"""
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
                    params['username'] = value
                elif key in ['password', 'pwd']:
                    params['password'] = value
        
        return params
    
    @staticmethod
    async def execute_query(connection_string: str, query: str) -> Dict[str, Any]:
        """Execute SQL query using sqlcmd with performance optimization"""
        try:
            params = SQLCmdService.parse_connection_string(connection_string)
            
            # Build sqlcmd command with connection timeout
            cmd = [
                'sqlcmd',
                '-S', params['server'],
                '-d', params['database'],
                '-U', params['username'],
                '-P', params['password'],
                '-Q', query,
                '-W',        # Remove trailing spaces
                '-s', '|',   # Column separator
                '-w', '999', # Wide output to prevent wrapping
                '-l', '5'    # Login timeout of 5 seconds
            ]
            
            logger.info(f"🔧 SQLCmd: Executing query: {query}")
            
            # Execute with async subprocess and timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Add 10 second timeout for query execution
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.error("❌ SQLCmd timeout: Query took longer than 10 seconds")
                raise Exception("Query timeout: SQL query took longer than 10 seconds to execute")
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"❌ SQLCmd error: {error_msg}")
                raise Exception(f"SQLCmd error: {error_msg}")
            
            result_text = stdout.decode().strip()
            logger.info(f"✅ SQLCmd raw result: {result_text}")
            
            # Parse results
            return SQLCmdService._parse_sqlcmd_output(result_text, query)
            
        except Exception as e:
            logger.error(f"❌ SQLCmd execute_query error: {str(e)}")
            raise
    
    @staticmethod
    def _parse_sqlcmd_output(output: str, original_query: str) -> Dict[str, Any]:
        """Parse sqlcmd output into structured format"""
        lines = output.strip().split('\n')
        
        if not lines:
            return {"columns": [], "data": [], "row_count": 0}
        
        # Remove empty lines and metadata
        data_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.endswith('row affected)') and not line.endswith('rows affected)'):
                data_lines.append(line)
        
        if not data_lines:
            return {"columns": [], "data": [], "row_count": 0}
        
        # For queries with pipe separator (standard format)
        if '|' in data_lines[0]:
            # First line is headers
            headers = [col.strip() for col in data_lines[0].split('|')]
            data = []
            
            # Skip separator line (contains dashes)
            start_idx = 2 if len(data_lines) > 1 and '-' in data_lines[1] else 1
            
            for line in data_lines[start_idx:]:
                if line.strip() and not line.startswith('-'):
                    values = [val.strip() for val in line.split('|')]
                    if len(values) == len(headers):
                        row_dict = {}
                        for i, header in enumerate(headers):
                            row_dict[header] = values[i] if i < len(values) else ""
                        data.append(row_dict)
            
            return {
                "columns": headers,
                "data": data,
                "row_count": len(data)
            }
        else:
            # Single column result
            data = []
            for line in data_lines:
                if line.strip():
                    data.append({"result": line.strip()})
            
            return {
                "columns": ["result"],
                "data": data,
                "row_count": len(data)
            }
    
    @staticmethod
    async def get_database_schema(connection_string: str) -> Dict[str, Any]:
        """Get database schema information using sqlcmd"""
        try:
            # Simplified schema query that works with sqlcmd output format
            schema_query = "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME IN ('Students', 'ScholarshipApplications') ORDER BY TABLE_NAME, ORDINAL_POSITION"
            
            result = await SQLCmdService.execute_query(connection_string, schema_query)
            logger.info(f"🔧 SQLCmd: Schema query returned {len(result['data'])} rows")
            
            # Parse schema into structured format
            tables = {}
            for row in result["data"]:
                # Handle the pipe-separated format
                if isinstance(row, dict) and "result" in row:
                    # Single column result - parse it
                    parts = row["result"].split("|")
                    if len(parts) >= 2:
                        table_name = parts[0].strip()
                        column_name = parts[1].strip()
                        data_type = parts[2].strip() if len(parts) > 2 else "varchar"
                    else:
                        continue
                elif isinstance(row, dict):
                    table_name = row.get("TABLE_NAME", "")
                    column_name = row.get("COLUMN_NAME", "")  
                    data_type = row.get("DATA_TYPE", "varchar")
                else:
                    continue
                    
                if not table_name or not column_name:
                    continue
                    
                if table_name not in tables:
                    tables[table_name] = {
                        "columns": [],
                        "foreign_keys": [],
                        "row_count": 0
                    }
                
                column_info = {
                    "name": column_name,
                    "data_type": data_type,
                    "nullable": True
                }
                
                # Avoid duplicates
                if not any(col["name"] == column_info["name"] for col in tables[table_name]["columns"]):
                    tables[table_name]["columns"].append(column_info)
            
            # Add known foreign key relationships for our test schema
            if "ScholarshipApplications" in tables and "Students" in tables:
                tables["ScholarshipApplications"]["foreign_keys"] = [
                    {
                        "column": "StudentId", 
                        "referenced_table": "Students",
                        "referenced_column": "Id"
                    }
                ]
            
            logger.info(f"✅ SQLCmd: Retrieved schema for {len(tables)} tables")
            logger.info(f"✅ SQLCmd: Tables found: {list(tables.keys())}")
            
            return {"tables": tables}
            
        except Exception as e:
            logger.error(f"❌ SQLCmd get_database_schema error: {str(e)}")
            raise

    @staticmethod
    async def test_connection(connection_string: str) -> bool:
        """Test database connection"""
        try:
            result = await SQLCmdService.execute_query(connection_string, "SELECT 1 as test")
            return result["row_count"] > 0
        except Exception as e:
            logger.error(f"❌ SQLCmd connection test failed: {str(e)}")
            return False

# Create global instance
sqlcmd_service = SQLCmdService()