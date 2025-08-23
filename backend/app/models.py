from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Connection(Base):
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    connection_string = Column(Text, nullable=False)  # Should be encrypted in production
    database_type = Column(String(50), default="mssql")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to enum files
    enum_files = relationship("EnumFile", back_populates="connection", cascade="all, delete-orphan")

class EnumFile(Base):
    __tablename__ = "enum_files"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # Path to the file on disk
    content_json = Column(Text, nullable=False)  # Cached JSON content of the file
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    connection = relationship("Connection", back_populates="enum_files")

class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, nullable=False)
    prompt = Column(Text, nullable=False)
    generated_sql = Column(Text)
    result_type = Column(String(50))  # 'text', 'table', 'error'
    result_data = Column(Text)  # JSON string
    execution_time = Column(Integer)  # milliseconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QueryHint(Base):
    __tablename__ = "query_hints"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # filtering, sorting, aggregation, etc.
    keywords = Column(Text, nullable=False)  # JSON array of keywords
    example_query = Column(Text, nullable=False)
    sql_pattern = Column(Text, nullable=False)
    description = Column(Text)
    tags = Column(Text)  # JSON array of tags
    popularity = Column(Integer, default=0)  # Usage count
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class QueryPattern(Base):
    __tablename__ = "query_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String(50), nullable=False, index=True)  # select, join, aggregate, etc.
    natural_language = Column(Text, nullable=False)
    sql_template = Column(Text, nullable=False)
    parameters = Column(Text)  # JSON object of parameters
    usage_count = Column(Integer, default=0)
    success_rate = Column(Integer, default=100)  # Percentage
    avg_execution_time = Column(Integer, default=0)  # milliseconds
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())