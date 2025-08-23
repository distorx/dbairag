from typing import Optional, Tuple, Dict, Any
import re
import httpx
import json
from ..config import settings

class OllamaService:
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate_sql(self, prompt: str, schema_info: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL from natural language prompt using Ollama"""
        
        system_prompt = """You are a SQL expert assistant. Convert natural language queries to valid MSSQL queries.
        
        Rules:
        1. Generate only valid MSSQL syntax
        2. Use appropriate JOIN clauses when multiple tables are mentioned
        3. Include proper WHERE clauses for filtering
        4. Use GROUP BY for aggregations
        5. Return ONLY the SQL query, no explanations or markdown formatting
        6. Do not include any backticks or code blocks
        
        {schema_info}
        """
        
        schema_context = f"Available schema:\n{schema_info}" if schema_info else ""
        
        full_prompt = f"""{system_prompt.format(schema_info=schema_context)}

User Query: {prompt}

SQL Query:"""
        
        try:
            # Call Ollama API
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                sql_query = result.get("response", "").strip()
                
                # Clean up the SQL query
                sql_query = self._clean_sql_query(sql_query)
                
                # Determine result type
                result_type = self._determine_result_type(sql_query)
                
                return sql_query, {"result_type": result_type}
            else:
                return self._basic_sql_generation(prompt)
        
        except Exception as e:
            print(f"Ollama error: {str(e)}")
            # Fallback to basic SQL generation
            return self._basic_sql_generation(prompt)
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean up SQL query from Ollama response"""
        # Remove markdown code blocks
        sql_query = re.sub(r'```sql\s*', '', sql_query)
        sql_query = re.sub(r'```\s*', '', sql_query)
        
        # Remove any explanatory text before SELECT/INSERT/UPDATE/DELETE
        lines = sql_query.split('\n')
        sql_lines = []
        sql_started = False
        
        for line in lines:
            line_upper = line.strip().upper()
            if not sql_started and any(line_upper.startswith(cmd) for cmd in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH']):
                sql_started = True
            
            if sql_started:
                sql_lines.append(line)
        
        return '\n'.join(sql_lines).strip()
    
    def _basic_sql_generation(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """Basic SQL generation without LLM"""
        prompt_lower = prompt.lower()
        
        # Simple pattern matching for common queries
        patterns = {
            r"show\s+tables?": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",
            r"show\s+databases?": "SELECT name FROM sys.databases",
            r"describe\s+(\w+)": "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{}'",
            r"count\s+.*\s+from\s+(\w+)": "SELECT COUNT(*) FROM {}",
            r"select\s+.*\s+from\s+(\w+)": prompt.upper() if prompt_lower.startswith("select") else f"SELECT * FROM {}"
        }
        
        for pattern, template in patterns.items():
            match = re.search(pattern, prompt_lower)
            if match:
                if "{}" in template and match.groups():
                    sql_query = template.format(match.group(1))
                else:
                    sql_query = template
                
                result_type = self._determine_result_type(sql_query)
                return sql_query, {"result_type": result_type}
        
        # If no pattern matches, return the prompt as-is (assuming it might be SQL)
        if any(keyword in prompt_lower for keyword in ['select', 'insert', 'update', 'delete', 'create', 'drop']):
            return prompt, {"result_type": self._determine_result_type(prompt)}
        
        return "", {"error": "Could not generate SQL from prompt", "result_type": "error"}
    
    def _determine_result_type(self, sql_query: str) -> str:
        """Determine if the result should be displayed as text or table"""
        sql_lower = sql_query.lower()
        
        # Queries that typically return tables
        table_indicators = [
            'select * from',
            'select top',
            'group by',
            'order by',
            'join',
            'where',
            'having'
        ]
        
        # Queries that typically return single values or messages
        text_indicators = [
            'count(*)',
            'sum(',
            'avg(',
            'max(',
            'min(',
            'select 1',
            'select @@'
        ]
        
        # Check for text indicators first (more specific)
        for indicator in text_indicators:
            if indicator in sql_lower:
                return "text"
        
        # Check for table indicators
        for indicator in table_indicators:
            if indicator in sql_lower:
                return "table"
        
        # Default based on query type
        if sql_lower.startswith('select'):
            return "table"
        else:
            return "text"
    
    async def list_models(self) -> list:
        """List available Ollama models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            print(f"Error listing Ollama models: {str(e)}")
            return []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()