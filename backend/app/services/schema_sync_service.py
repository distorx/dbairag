"""
Service to synchronize database schema to local cache
"""
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
import logging

from ..models import CachedSchema, SchemaRelationship, SchemaSyncStatus
from .schema_analyzer_universal import UniversalSchemaAnalyzer as SchemaAnalyzer

logger = logging.getLogger(__name__)

class SchemaSyncService:
    def __init__(self):
        self.schema_analyzer = SchemaAnalyzer()
        self.sync_timeout = 10  # Reduced to 10 seconds timeout for sync
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
    
    async def check_and_sync_schema(
        self, 
        connection_id: int, 
        connection_string: str,
        db_session: AsyncSession,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Check if schema is cached locally and sync if needed.
        Returns the schema info and sync status.
        """
        start_time = datetime.now()
        
        # Check sync status
        sync_status = await self._get_sync_status(connection_id, db_session)
        
        # Determine if sync is needed
        needs_sync = await self._needs_sync(connection_id, sync_status, db_session, force_refresh)
        
        if needs_sync:
            logger.info(f"Schema sync needed for connection {connection_id}")
            
            # Update sync status to in_progress
            await self._update_sync_status(
                connection_id, 
                db_session,
                status="in_progress",
                started_at=start_time
            )
            
            try:
                # Perform sync with timeout
                schema_info = await asyncio.wait_for(
                    self._sync_schema(connection_id, connection_string, db_session),
                    timeout=self.sync_timeout
                )
                
                # Update sync status to completed
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                await self._update_sync_status(
                    connection_id,
                    db_session,
                    status="completed",
                    completed_at=datetime.now(),
                    duration_ms=duration_ms,
                    tables_synced=len(schema_info.get("tables", {})),
                    schema_hash=self._calculate_schema_hash(schema_info)
                )
                
                logger.info(f"Schema sync completed for connection {connection_id} in {duration_ms}ms")
                
            except asyncio.TimeoutError:
                error_msg = f"Schema sync timeout after {self.sync_timeout} seconds"
                logger.error(error_msg)
                
                await self._update_sync_status(
                    connection_id,
                    db_session,
                    status="failed",
                    error_message=error_msg
                )
                
                # Try to load partial cache if available
                schema_info = await self._load_cached_schema(connection_id, db_session)
                
            except Exception as e:
                error_msg = f"Schema sync failed: {str(e)}"
                logger.error(error_msg)
                
                await self._update_sync_status(
                    connection_id,
                    db_session,
                    status="failed",
                    error_message=error_msg
                )
                
                # Try to load cached schema as fallback
                schema_info = await self._load_cached_schema(connection_id, db_session)
        else:
            logger.info(f"Using cached schema for connection {connection_id}")
            schema_info = await self._load_cached_schema(connection_id, db_session)
        
        # Add sync metadata to schema info
        if schema_info:
            schema_info["sync_metadata"] = {
                "cached": not needs_sync,
                "last_synced": sync_status.last_sync_completed.isoformat() if sync_status and sync_status.last_sync_completed else None,
                "sync_status": sync_status.sync_status if sync_status else "unknown"
            }
        
        return schema_info
    
    async def _needs_sync(
        self,
        connection_id: int,
        sync_status: Optional[SchemaSyncStatus],
        db_session: AsyncSession,
        force_refresh: bool
    ) -> bool:
        """
        Determine if schema sync is needed.
        """
        if force_refresh:
            return True
        
        if not sync_status:
            return True
        
        if sync_status.sync_status != "completed":
            return True
        
        # Check if cache is expired
        if sync_status.last_sync_completed:
            if datetime.now() - sync_status.last_sync_completed > self.cache_duration:
                return True
        else:
            return True
        
        # Check if we have cached tables
        result = await db_session.execute(
            select(CachedSchema).where(CachedSchema.connection_id == connection_id).limit(1)
        )
        cached_table = result.scalar_one_or_none()
        
        if not cached_table:
            return True
        
        return False
    
    async def _sync_schema(
        self,
        connection_id: int,
        connection_string: str,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Sync schema from database to local cache.
        """
        # Create engine and get schema
        engine = self.schema_analyzer.create_engine(connection_string)
        
        # Get schema with enhanced analysis
        schema_info = await self.schema_analyzer.get_database_schema(
            engine, 
            str(connection_id),
            force_refresh=True
        )
        
        # Clear old cache
        await db_session.execute(
            delete(CachedSchema).where(CachedSchema.connection_id == connection_id)
        )
        await db_session.execute(
            delete(SchemaRelationship).where(SchemaRelationship.connection_id == connection_id)
        )
        
        # Store tables in cache
        for table_name, table_info in schema_info.get("tables", {}).items():
            cached_schema = CachedSchema(
                connection_id=connection_id,
                table_name=table_name,
                table_type=table_info.get("type", "TABLE"),
                row_count=table_info.get("row_count", 0),
                columns_json=table_info.get("columns", []),
                primary_keys_json=table_info.get("primary_keys", []),
                foreign_keys_json=table_info.get("foreign_keys", []),
                sample_data_json=table_info.get("sample_data", [])[:5],  # Limit samples
                last_synced=datetime.now()
            )
            db_session.add(cached_schema)
        
        # Store relationships
        for rel in schema_info.get("relationships", []):
            schema_rel = SchemaRelationship(
                connection_id=connection_id,
                from_table=rel.get("from_table"),
                from_column=rel.get("from_column"),
                to_table=rel.get("to_table"),
                to_column=rel.get("to_column"),
                relationship_type=rel.get("type", "foreign_key"),
                confidence=int(rel.get("confidence", 1.0) * 100)
            )
            db_session.add(schema_rel)
        
        await db_session.commit()
        
        return schema_info
    
    async def _load_cached_schema(
        self,
        connection_id: int,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Load schema from local cache.
        """
        # Load cached tables
        result = await db_session.execute(
            select(CachedSchema).where(CachedSchema.connection_id == connection_id)
        )
        cached_tables = result.scalars().all()
        
        if not cached_tables:
            return None
        
        # Load relationships
        result = await db_session.execute(
            select(SchemaRelationship).where(SchemaRelationship.connection_id == connection_id)
        )
        cached_relationships = result.scalars().all()
        
        # Build schema info from cache
        schema_info = {
            "tables": {},
            "relationships": [],
            "statistics": {},
            "analyzed_at": None
        }
        
        for cached_table in cached_tables:
            schema_info["tables"][cached_table.table_name] = {
                "type": cached_table.table_type,
                "columns": cached_table.columns_json or [],
                "primary_keys": cached_table.primary_keys_json or [],
                "foreign_keys": cached_table.foreign_keys_json or [],
                "row_count": cached_table.row_count,
                "sample_data": cached_table.sample_data_json or []
            }
            
            if cached_table.last_synced and (not schema_info["analyzed_at"] or cached_table.last_synced > datetime.fromisoformat(schema_info["analyzed_at"])):
                schema_info["analyzed_at"] = cached_table.last_synced.isoformat()
        
        for rel in cached_relationships:
            schema_info["relationships"].append({
                "from_table": rel.from_table,
                "from_column": rel.from_column,
                "to_table": rel.to_table,
                "to_column": rel.to_column,
                "type": rel.relationship_type,
                "confidence": rel.confidence / 100.0
            })
        
        # Calculate statistics
        schema_info["statistics"] = {
            "total_tables": len(schema_info["tables"]),
            "total_columns": sum(len(t.get("columns", [])) for t in schema_info["tables"].values()),
            "total_relationships": len(schema_info["relationships"]),
            "total_rows": sum(t.get("row_count", 0) for t in schema_info["tables"].values())
        }
        
        return schema_info
    
    async def _get_sync_status(
        self,
        connection_id: int,
        db_session: AsyncSession
    ) -> Optional[SchemaSyncStatus]:
        """
        Get current sync status for connection.
        """
        result = await db_session.execute(
            select(SchemaSyncStatus).where(SchemaSyncStatus.connection_id == connection_id)
        )
        return result.scalar_one_or_none()
    
    async def _update_sync_status(
        self,
        connection_id: int,
        db_session: AsyncSession,
        status: str = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        duration_ms: int = None,
        tables_synced: int = None,
        error_message: str = None,
        schema_hash: str = None
    ):
        """
        Update or create sync status record.
        """
        result = await db_session.execute(
            select(SchemaSyncStatus).where(SchemaSyncStatus.connection_id == connection_id)
        )
        sync_status = result.scalar_one_or_none()
        
        if not sync_status:
            sync_status = SchemaSyncStatus(connection_id=connection_id)
            db_session.add(sync_status)
        
        if status:
            sync_status.sync_status = status
        if started_at:
            sync_status.last_sync_started = started_at
        if completed_at:
            sync_status.last_sync_completed = completed_at
        if duration_ms is not None:
            sync_status.sync_duration_ms = duration_ms
        if tables_synced is not None:
            sync_status.tables_synced = tables_synced
        if error_message:
            sync_status.error_message = error_message
        if schema_hash:
            sync_status.schema_hash = schema_hash
        
        await db_session.commit()
    
    def _calculate_schema_hash(self, schema_info: Dict[str, Any]) -> str:
        """
        Calculate hash of schema structure for change detection.
        """
        if not schema_info or "tables" not in schema_info:
            return ""
        
        # Create a simplified structure for hashing
        schema_structure = {
            "tables": sorted(schema_info["tables"].keys()),
            "columns": {}
        }
        
        for table_name, table_info in sorted(schema_info["tables"].items()):
            columns = table_info.get("columns", [])
            schema_structure["columns"][table_name] = sorted([
                f"{col.get('name')}:{col.get('data_type')}" 
                for col in columns
            ])
        
        # Calculate hash
        schema_json = json.dumps(schema_structure, sort_keys=True)
        return hashlib.sha256(schema_json.encode()).hexdigest()
    
    async def get_sync_statistics(
        self,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get overall sync statistics.
        """
        result = await db_session.execute(select(SchemaSyncStatus))
        all_status = result.scalars().all()
        
        stats = {
            "total_connections": len(all_status),
            "synced_connections": sum(1 for s in all_status if s.sync_status == "completed"),
            "failed_connections": sum(1 for s in all_status if s.sync_status == "failed"),
            "in_progress": sum(1 for s in all_status if s.sync_status == "in_progress"),
            "average_sync_time_ms": 0,
            "total_tables_cached": 0
        }
        
        # Calculate average sync time
        sync_times = [s.sync_duration_ms for s in all_status if s.sync_duration_ms]
        if sync_times:
            stats["average_sync_time_ms"] = sum(sync_times) / len(sync_times)
        
        # Count total cached tables
        result = await db_session.execute(
            select(CachedSchema.connection_id, CachedSchema.table_name)
        )
        stats["total_tables_cached"] = len(result.all())
        
        return stats