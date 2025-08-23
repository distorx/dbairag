from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./connections.db"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_enabled: bool = True
    
    # Cache TTL settings (in seconds)
    cache_ttl_schema: int = 3600  # 1 hour
    cache_ttl_enums: int = 7200  # 2 hours
    cache_ttl_sql: int = 1800  # 30 minutes
    cache_ttl_query_result: int = 600  # 10 minutes
    
    # CORS
    frontend_url: str = "http://localhost:4200"
    
    class Config:
        env_file = ".env"

settings = Settings()