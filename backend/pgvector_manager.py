"""
PostgreSQL Vector Manager using pgvector
Replaces CyborgDB with a simpler, free-tier compatible solution
"""

import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
import asyncpg
from pgvector.asyncpg import register_vector
import numpy as np

from backend.exceptions import (
    ServiceInitializationError,
    SearchError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class PgVectorManager:
    """Manages vector storage and search using PostgreSQL + pgvector"""
    
    _pool = None
    _initialized = False
    
    def __init__(self):
        """Initialize connection pool"""
        if not PgVectorManager._initialized:
            raise ServiceInitializationError(
                "PgVectorManager",
                "Manager not initialized. Call initialize() first."
            )
    
    @classmethod
    async def initialize(cls):
        """Initialize the PostgreSQL connection pool and create tables"""
        if cls._initialized:
            return
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ServiceInitializationError(
                "PgVectorManager",
                "Missing DATABASE_URL environment variable"
            )
        
        # Clean connection string (remove channel_binding if present)
        database_url = database_url.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?")
        
        try:
            # Create connection pool
            cls._pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Register pgvector type
            async with cls._pool.acquire() as conn:
                await register_vector(conn)
                
                # Create extension if not exists
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Create vectors table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS patient_vectors (
                        id TEXT PRIMARY KEY,
                        patient_id TEXT NOT NULL,
                        embedding vector(768),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Create index for vector similarity search
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS patient_vectors_embedding_idx 
                    ON patient_vectors 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)
                
                # Create index for patient_id lookups
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS patient_vectors_patient_id_idx 
                    ON patient_vectors (patient_id)
                """)
            
            cls._initialized = True
            logger.info("✅ PgVector initialized successfully")
            logger.info("   Backend: PostgreSQL with pgvector extension")
            logger.info("   Storage: Persistent in database")
            logger.info("   Search: IVFFlat index with cosine similarity")
            
        except Exception as e:
            raise ServiceInitializationError(
                "PgVectorManager",
                f"Failed to initialize: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    @classmethod
    async def close(cls):
        """Close the connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._initialized = False
    
    async def upsert(self, items: List[Dict[str, Any]]) -> None:
        """
        Insert or update vectors
        
        Args:
            items: List of dicts with 'id', 'vector', 'patient_id', and 'metadata'
        """
        if not self._pool:
            raise DatabaseError("upsert", "Connection pool not initialized")
        
        try:
            async with self._pool.acquire() as conn:
                # Prepare data for batch insert
                records = [
                    (
                        item['id'],
                        item.get('patient_id', item['id']),
                        item['vector'],
                        json.dumps(item.get('metadata', {}))
                    )
                    for item in items
                ]
                
                # Batch upsert
                await conn.executemany("""
                    INSERT INTO patient_vectors (id, patient_id, embedding, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) 
                    DO UPDATE SET 
                        patient_id = EXCLUDED.patient_id,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, records)
                
                logger.debug(f"Upserted {len(items)} vectors")
                
        except Exception as e:
            raise DatabaseError(
                "upsert",
                f"Failed to upsert vectors: {str(e)}",
                details={"error_type": type(e).__name__, "item_count": len(items)}
            )
    
    async def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        patient_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            patient_id: Optional filter by patient_id
            
        Returns:
            List of results with id, patient_id, metadata, and distance
        """
        if not self._pool:
            raise SearchError("Vector search failed", "Connection pool not initialized")
        
        try:
            async with self._pool.acquire() as conn:
                await register_vector(conn)
                
                if patient_id:
                    # Search within specific patient
                    results = await conn.fetch("""
                        SELECT 
                            id,
                            patient_id,
                            metadata,
                            1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        WHERE patient_id = $2
                        ORDER BY embedding <=> $1::vector
                        LIMIT $3
                    """, query_vector, patient_id, top_k)
                else:
                    # Search across all patients
                    results = await conn.fetch("""
                        SELECT 
                            id,
                            patient_id,
                            metadata,
                            1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                    """, query_vector, top_k)
                
                # Convert to list of dicts
                return [
                    {
                        'id': row['id'],
                        'patient_id': row['patient_id'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'similarity': float(row['similarity'])
                    }
                    for row in results
                ]
                
        except Exception as e:
            raise SearchError(
                "Vector search failed",
                str(e),
                details={"error_type": type(e).__name__, "top_k": top_k}
            )
    
    async def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve vectors by IDs
        
        Args:
            ids: List of vector IDs
            
        Returns:
            List of vectors with metadata
        """
        if not self._pool:
            raise DatabaseError("get", "Connection pool not initialized")
        
        try:
            async with self._pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT id, patient_id, embedding, metadata
                    FROM patient_vectors
                    WHERE id = ANY($1::text[])
                """, ids)
                
                return [
                    {
                        'id': row['id'],
                        'patient_id': row['patient_id'],
                        'vector': list(row['embedding']),
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                    }
                    for row in results
                ]
                
        except Exception as e:
            raise DatabaseError(
                "get",
                f"Failed to retrieve vectors: {str(e)}",
                details={"error_type": type(e).__name__, "id_count": len(ids)}
            )
    
    async def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs"""
        if not self._pool:
            raise DatabaseError("delete", "Connection pool not initialized")
        
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM patient_vectors
                    WHERE id = ANY($1::text[])
                """, ids)
                
                logger.debug(f"Deleted {len(ids)} vectors")
                
        except Exception as e:
            raise DatabaseError(
                "delete",
                f"Failed to delete vectors: {str(e)}",
                details={"error_type": type(e).__name__, "id_count": len(ids)}
            )
    
    async def count(self) -> int:
        """Get total number of vectors"""
        if not self._pool:
            raise DatabaseError("count", "Connection pool not initialized")
        
        try:
            async with self._pool.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM patient_vectors")
                return result
                
        except Exception as e:
            raise DatabaseError(
                "count",
                f"Failed to count vectors: {str(e)}",
                details={"error_type": type(e).__name__}
            )


# Singleton instance
_manager_instance = None


async def get_pgvector_manager() -> PgVectorManager:
    """Get or create the PgVector manager instance"""
    global _manager_instance
    
    if _manager_instance is None:
        await PgVectorManager.initialize()
        _manager_instance = PgVectorManager()
    
    return _manager_instance
