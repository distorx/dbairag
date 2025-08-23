from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class ResultType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    ERROR = "error"

class QueryType(str, Enum):
    SELECT = "select"
    COUNT = "count"
    AGGREGATE = "aggregate"
    JOIN = "join"
    CUSTOM = "custom"

class TableType(str, Enum):
    BASE_TABLE = "BASE TABLE"
    VIEW = "VIEW"

class DataTypeCategory(str, Enum):
    NUMERIC = "numeric"
    TEXT = "text"
    DATE = "date"
    BOOLEAN = "boolean"
    BINARY = "binary"
    JSON = "json"
    OTHER = "other"

# Connection Schemas
class ConnectionBase(BaseModel):
    name: str
    connection_string: str
    database_type: str = "mssql"
    is_active: bool = True

class ConnectionCreate(ConnectionBase):
    pass

class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    connection_string: Optional[str] = None
    database_type: Optional[str] = None
    is_active: Optional[bool] = None

class Connection(ConnectionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Query Schemas
class QueryRequest(BaseModel):
    connection_id: int
    prompt: str
    
class QueryResponse(BaseModel):
    id: Optional[int] = None
    prompt: str
    generated_sql: Optional[str] = None
    result_type: ResultType
    result_data: Union[str, List[Dict[str, Any]], Dict[str, Any]]
    execution_time: Optional[int] = None
    created_at: Optional[datetime] = None

# Cell Schema (for Jupyter-like interface)
class Cell(BaseModel):
    id: str
    type: str = "prompt"  # 'prompt' or 'response'
    content: str
    result_type: Optional[ResultType] = None
    result_data: Optional[Union[str, List[Dict[str, Any]]]] = None
    execution_time: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)

class NotebookSession(BaseModel):
    id: str
    connection_id: int
    cells: List[Cell] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Schema Information Models
class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool
    category: Optional[DataTypeCategory] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False

class TableInfo(BaseModel):
    name: str
    type: TableType
    columns: List[ColumnInfo]
    row_count: int
    primary_keys: List[str]
    foreign_keys: List[Dict[str, str]]  # {column: referenced_table.referenced_column}

class DatabaseSchema(BaseModel):
    tables: List[TableInfo]
    total_tables: int
    total_rows: int
    analyzed_at: Optional[datetime] = None

# Query Suggestions
class QueryTemplate(BaseModel):
    name: str
    description: str
    query_type: QueryType
    template: str
    parameters: List[str] = []
    
class QuerySuggestions(BaseModel):
    tables: List[str]
    common_queries: List[QueryTemplate]
    aggregation_columns: Dict[str, List[str]]  # table -> numeric columns
    filter_columns: Dict[str, List[str]]  # table -> filterable columns