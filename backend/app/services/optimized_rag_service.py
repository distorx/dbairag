import time
import logging
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..config import settings

logger = logging.getLogger(__name__)

class OptimizedRAGService:
    """Modern, high-performance RAG service using LangChain best practices"""
    
    def __init__(self):
        self.llm = None
        self.performance_metrics = {}
        
        if settings.openai_api_key:
            try:
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model="gpt-4o-mini",  # Faster, cheaper model
                    temperature=0,
                    max_tokens=200,  # Limit for SQL queries
                    timeout=10.0  # 10 second timeout
                )
                logger.info("🚀 OptimizedRAGService: OpenAI configured with gpt-4o-mini")
            except Exception as e:
                logger.error(f"❌ OptimizedRAGService: OpenAI initialization failed: {e}")
                self.llm = None
        else:
            logger.info("⚠️ OptimizedRAGService: No OpenAI API key, using pattern matching only")
    
    @lru_cache(maxsize=50)
    def _get_schema_context(self, connection_id: str, schema_hash: str) -> str:
        """Cached schema context building - much faster than DB queries"""
        # This will be populated by the calling code
        return f"Schema context for connection {connection_id}"
    
    def _build_optimized_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Build minimal, focused schema context for LLM"""
        if not schema_info or "tables" not in schema_info:
            return "No schema information available"
        
        context = "Database Schema:\n"
        tables = schema_info["tables"]
        
        # Focus on key tables and relationships
        for table_name, table_data in list(tables.items())[:5]:  # Limit to 5 tables
            context += f"\n{table_name}:\n"
            
            # Key columns only
            columns = table_data.get("columns", [])[:10]  # Limit columns
            for col in columns:
                context += f"  - {col['name']} ({col['data_type']})\n"
            
            # Foreign key relationships - CRITICAL for JOINs
            fks = table_data.get("foreign_keys", [])
            if fks:
                context += "  Relationships:\n"
                for fk in fks:
                    context += f"    {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}\n"
        
        # Add common patterns
        context += "\nCommon Patterns:\n"
        context += "- 'count X with Y' = JOIN tables and COUNT DISTINCT\n"
        context += "- Always use WITH (NOLOCK) for SELECT queries\n"
        
        return context
    
    def _pattern_match_sql(self, prompt: str, schema_info: Dict[str, Any]) -> Optional[str]:
        """Fast pattern matching for common queries"""
        prompt_lower = prompt.lower().strip()
        
        # Common pattern: count students with applications  
        if all(word in prompt_lower for word in ["count", "student", "application"]):
            logger.info("🎯 Pattern matched: count students with applications")
            return "SELECT COUNT(DISTINCT s.Id) AS total FROM Students s WITH (NOLOCK) INNER JOIN ScholarshipApplications sa WITH (NOLOCK) ON s.Id = sa.StudentId"
        
        # Pattern: show all students (handle both singular and plural)
        if "show" in prompt_lower and "student" in prompt_lower:
            logger.info("🎯 Pattern matched: show students")
            return "SELECT TOP 100 * FROM Students WITH (NOLOCK)"
        
        # Pattern: count total students (handle both singular and plural)
        if "count" in prompt_lower and "student" in prompt_lower and "application" not in prompt_lower:
            logger.info("🎯 Pattern matched: count total students")
            return "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK)"
        
        return None
    
    async def generate_sql_optimized(self, prompt: str, schema_info: Optional[Dict[str, Any]] = None, connection_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Optimized SQL generation with performance logging"""
        start_time = time.time()
        
        logger.info(f"🚀 OptimizedRAG: Starting SQL generation for: '{prompt}'")
        logger.info(f"🔧 OptimizedRAG: LLM available: {self.llm is not None}")
        
        metadata = {"method": "unknown", "cached": False, "performance": {}}
        
        try:
            # Step 1: Fast pattern matching (< 1ms)
            pattern_start = time.time()
            pattern_sql = self._pattern_match_sql(prompt, schema_info or {})
            pattern_time = time.time() - pattern_start
            
            if pattern_sql:
                metadata.update({
                    "method": "pattern_matching",
                    "pattern_match_time": f"{pattern_time*1000:.2f}ms",
                    "result_type": "table"
                })
                total_time = time.time() - start_time
                logger.info(f"✅ OptimizedRAG: Pattern match completed in {total_time*1000:.2f}ms")
                return pattern_sql, metadata
            
            # Step 2: LLM generation with optimized prompt
            if not self.llm:
                logger.warning("⚠️ OptimizedRAG: No LLM available, using basic fallback")
                fallback_sql = "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK)"
                metadata.update({
                    "method": "fallback",
                    "result_type": "table"
                })
                return fallback_sql, metadata
            
            # Build optimized context
            context_start = time.time()
            schema_context = self._build_optimized_schema_context(schema_info or {})
            context_time = time.time() - context_start
            
            # Optimized prompt template
            system_prompt = """You are an expert MSSQL query generator. Generate ONLY the SQL query, no explanations.

Rules:
- For "count X with Y": use INNER JOIN and COUNT DISTINCT
- Always add WITH (NOLOCK) for SELECT queries  
- Use proper MSSQL syntax

{schema_context}

Query request: {prompt}

SQL:"""
            
            # Fast LLM call
            llm_start = time.time()
            messages = [
                SystemMessage(content=system_prompt.format(
                    schema_context=schema_context,
                    prompt=prompt
                ))
            ]
            
            response = await self.llm.ainvoke(messages)
            sql_query = response.content.strip()
            
            # Clean up response
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            if sql_query.endswith(";"):
                sql_query = sql_query[:-1]
            
            llm_time = time.time() - llm_start
            total_time = time.time() - start_time
            
            metadata.update({
                "method": "llm_optimized",
                "context_time": f"{context_time*1000:.2f}ms",
                "llm_time": f"{llm_time*1000:.2f}ms",
                "total_time": f"{total_time*1000:.2f}ms",
                "result_type": "table",
                "schema_context_length": len(schema_context)
            })
            
            logger.info(f"✅ OptimizedRAG: LLM generation completed in {total_time*1000:.2f}ms")
            logger.info(f"🎯 OptimizedRAG: Generated SQL: {sql_query}")
            
            return sql_query, metadata
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"❌ OptimizedRAG: Error after {error_time*1000:.2f}ms: {str(e)}")
            
            # Fallback on error
            fallback_sql = "SELECT COUNT(*) AS total FROM Students WITH (NOLOCK)"
            metadata.update({
                "method": "error_fallback",
                "error": str(e),
                "error_time": f"{error_time*1000:.2f}ms",
                "result_type": "table"
            })
            return fallback_sql, metadata
    
    def log_performance_metrics(self, operation: str, duration_ms: float, metadata: Dict[str, Any]):
        """Log detailed performance metrics"""
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []
        
        self.performance_metrics[operation].append({
            "timestamp": time.time(),
            "duration_ms": duration_ms,
            "metadata": metadata
        })
        
        # Keep only last 100 records per operation
        if len(self.performance_metrics[operation]) > 100:
            self.performance_metrics[operation] = self.performance_metrics[operation][-100:]
        
        logger.info(f"📊 Performance: {operation} completed in {duration_ms:.2f}ms")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        summary = {}
        for operation, metrics in self.performance_metrics.items():
            if metrics:
                durations = [m["duration_ms"] for m in metrics]
                summary[operation] = {
                    "count": len(metrics),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "recent_methods": [m["metadata"].get("method") for m in metrics[-10:]]
                }
        return summary

# Global instance
optimized_rag_service = OptimizedRAGService()