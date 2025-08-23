"""
Schema cache model for storing database schema information locally
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from ..database import Base

class CachedSchema(Base):
    __tablename__ = "cached_schemas"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)
    table_name = Column(String(255), nullable=False, index=True)
    table_type = Column(String(50))  # TABLE or VIEW
    row_count = Column(Integer, default=0)
    columns_json = Column(JSON)  # Store column information as JSON
    primary_keys_json = Column(JSON)  # Store primary keys as JSON
    foreign_keys_json = Column(JSON)  # Store foreign keys as JSON
    sample_data_json = Column(JSON)  # Store sample data as JSON
    last_synced = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SchemaRelationship(Base):
    __tablename__ = "schema_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, index=True)
    from_table = Column(String(255), nullable=False)
    from_column = Column(String(255), nullable=False)
    to_table = Column(String(255), nullable=False)
    to_column = Column(String(255), nullable=False)
    relationship_type = Column(String(50))  # foreign_key, inferred, semantic
    confidence = Column(Integer, default=100)  # 0-100 confidence score
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SchemaSyncStatus(Base):
    __tablename__ = "schema_sync_status"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False, unique=True)
    last_sync_started = Column(DateTime(timezone=True))
    last_sync_completed = Column(DateTime(timezone=True))
    sync_status = Column(String(50))  # pending, in_progress, completed, failed
    sync_duration_ms = Column(Integer)
    tables_synced = Column(Integer, default=0)
    error_message = Column(Text)
    schema_hash = Column(String(255))  # Hash to detect schema changes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())