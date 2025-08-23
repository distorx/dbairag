from typing import Optional, Tuple, Dict, Any
import re
from ..config import settings
from .ollama_service import OllamaService

class RAGService:
    def __init__(self):
        self.llm = None
        self.use_ollama = True  # Default to Ollama
        self.ollama_service = None
        
        # Try to initialize Ollama first
        if self.use_ollama:
            self.ollama_service = OllamaService(
                model=getattr(settings, 'ollama_model', 'llama3.2'),
                base_url=getattr(settings, 'ollama_url', 'http://localhost:11434')
            )
        # Fallback to OpenAI if configured
        elif settings.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage, SystemMessage
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model="gpt-4",
                    temperature=0.1
                )
                self.use_ollama = False
            except ImportError:
                print("OpenAI libraries not available, using Ollama")
    
    async def generate_sql(self, prompt: str, schema_info: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL from natural language prompt"""
        
        # Try Ollama first
        if self.ollama_service:
            return await self.ollama_service.generate_sql(prompt, schema_info)
        
        # Fallback to OpenAI if available
        if self.llm and not self.use_ollama:
            return await self._generate_sql_openai(prompt, schema_info)
        
        # Final fallback to pattern matching
        return self._basic_sql_generation(prompt)
    
    async def _generate_sql_openai(self, prompt: str, schema_info: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL using OpenAI"""
        from langchain.schema import HumanMessage, SystemMessage
        
        system_prompt = """You are a SQL expert assistant. Convert natural language queries to valid MSSQL queries.
        
        Rules:
        1. Generate only valid MSSQL syntax
        2. Use appropriate JOIN clauses when multiple tables are mentioned
        3. Include proper WHERE clauses for filtering
        4. Use GROUP BY for aggregations
        5. Return ONLY the SQL query, no explanations
        
        {schema_info}
        
        Output format:
        - If the result should be a table, generate a SELECT query
        - If the result is a single value or message, still use SELECT but indicate it's text
        - Always validate the SQL syntax
        """
        
        schema_context = f"Available schema:\n{schema_info}" if schema_info else ""
        
        messages = [
            SystemMessage(content=system_prompt.format(schema_info=schema_context)),
            HumanMessage(content=f"Convert this to SQL: {prompt}")
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            sql_query = response.content.strip()
            
            # Clean up the SQL query
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            # Determine result type
            result_type = self._determine_result_type(sql_query)
            
            return sql_query, {"result_type": result_type}
        
        except Exception as e:
            return "", {"error": str(e), "result_type": "error"}
    
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
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Get available models from Ollama or return OpenAI status"""
        if self.ollama_service:
            models = await self.ollama_service.list_models()
            return {
                "provider": "ollama",
                "models": models,
                "current_model": self.ollama_service.model
            }
        elif self.llm:
            return {
                "provider": "openai",
                "models": ["gpt-4"],
                "current_model": "gpt-4"
            }
        else:
            return {
                "provider": "basic",
                "models": [],
                "current_model": "pattern-matching"
            }