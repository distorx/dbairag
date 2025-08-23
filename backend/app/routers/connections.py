from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
from ..database import get_db
from ..models import Connection as ConnectionModel
from ..schemas import Connection, ConnectionCreate, ConnectionUpdate
from ..services.mssql_service import MSSQLService

router = APIRouter(prefix="/api/connections", tags=["connections"])

@router.get("/", response_model=List[Connection])
async def get_connections(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all connections"""
    result = await db.execute(
        select(ConnectionModel).offset(skip).limit(limit)
    )
    connections = result.scalars().all()
    return connections

@router.get("/{connection_id}", response_model=Connection)
async def get_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific connection"""
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    return connection

@router.post("/", response_model=Connection)
async def create_connection(
    connection: ConnectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new connection"""
    # Test the connection first
    is_valid, message = await MSSQLService.test_connection_async(connection.connection_string)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {message}"
        )
    
    # Check if name already exists
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.name == connection.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection name already exists"
        )
    
    # Create new connection
    db_connection = ConnectionModel(**connection.dict())
    db.add(db_connection)
    await db.commit()
    await db.refresh(db_connection)
    
    return db_connection

@router.put("/{connection_id}", response_model=Connection)
async def update_connection(
    connection_id: int,
    connection_update: ConnectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a connection"""
    # Get existing connection
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Test new connection string if provided
    if connection_update.connection_string:
        is_valid, message = await MSSQLService.test_connection_async(connection_update.connection_string)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed: {message}"
            )
    
    # Update connection
    update_data = connection_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(connection, field, value)
    
    await db.commit()
    await db.refresh(connection)
    
    return connection

@router.delete("/{connection_id}")
async def delete_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a connection"""
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    await db.delete(connection)
    await db.commit()
    
    return {"message": "Connection deleted successfully"}

@router.post("/{connection_id}/test")
async def test_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Test a connection"""
    result = await db.execute(
        select(ConnectionModel).where(ConnectionModel.id == connection_id)
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    is_valid, message = await MSSQLService.test_connection_async(connection.connection_string)
    
    return {
        "success": is_valid,
        "message": message
    }