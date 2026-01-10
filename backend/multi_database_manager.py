"""
Multi-Database Manager for CipherCare
Uses 4 databases to maximize storage:
- DB1: User authentication (Neon)
- DB2: Patient vectors part 1 (Neon) - 50,000 records
- DB3: Patient vectors part 2 (Neon) - 56,000 records
- DB4: Patient vectors part 3 (Neon) - 5,060 records
"""

import os
import asyncpg
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MultiDatabaseManager:
    """Manages multiple databases for different purposes"""
    
    def __init__(self):
        # Database 1: User authentication
        self.auth_db_url = os.getenv("AUTH_DATABASE_URL")
        
        # Database 2: Patient vectors (part 1)
        self.vectors_db1_url = os.getenv("VECTORS_DB1_URL")
        
        # Database 3: Patient vectors (part 2)
        self.vectors_db2_url = os.getenv("VECTORS_DB2_URL")
        
        # Database 4: Patient vectors (part 3)
        self.vectors_db3_url = os.getenv("VECTORS_DB3_URL")
        
        self.auth_pool = None
        self.vectors_pool1 = None
        self.vectors_pool2 = None
        self.vectors_pool3 = None
        
        # Sharding strategy: split by patient_id
        self.shard_threshold_1 = 50000  # First 50K in DB1
        self.shard_threshold_2 = 106000  # Next 56K in DB2, rest in DB3
    
    async def initialize(self):
        """Initialize all database connections"""
        
        # Initialize auth database
        if self.auth_db_url:
            self.auth_pool = await asyncpg.create_pool(
                self.auth_db_url.replace("&channel_binding=require", ""),
                min_size=2,
                max_size=5
            )
            logger.info("✅ Auth database connected")
        
        # Initialize vector database 1
        if self.vectors_db1_url:
            self.vectors_pool1 = await asyncpg.create_pool(
                self.vectors_db1_url.replace("&channel_binding=require", ""),
                min_size=2,
                max_size=5
            )
            
            # Create tables and indexes
            async with self.vectors_pool1.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS patient_vectors (
                        id TEXT PRIMARY KEY,
                        patient_id TEXT NOT NULL,
                        embedding vector(768),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS patient_vectors_patient_id_idx 
                    ON patient_vectors (patient_id)
                """)
            
            logger.info("✅ Vector database 1 connected")
        
        # Initialize vector database 2
        if self.vectors_db2_url:
            self.vectors_pool2 = await asyncpg.create_pool(
                self.vectors_db2_url.replace("&channel_binding=require", ""),
                min_size=2,
                max_size=5
            )
            
            # Create tables and indexes
            async with self.vectors_pool2.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS patient_vectors (
                        id TEXT PRIMARY KEY,
                        patient_id TEXT NOT NULL,
                        embedding vector(768),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS patient_vectors_patient_id_idx 
                    ON patient_vectors (patient_id)
                """)
            
            logger.info("✅ Vector database 2 connected")
        
        # Initialize vector database 3
        if self.vectors_db3_url:
            self.vectors_pool3 = await asyncpg.create_pool(
                self.vectors_db3_url.replace("&channel_binding=require", ""),
                min_size=2,
                max_size=5
            )
            
            # Create tables and indexes
            async with self.vectors_pool3.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS patient_vectors (
                        id TEXT PRIMARY KEY,
                        patient_id TEXT NOT NULL,
                        embedding vector(768),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS patient_vectors_patient_id_idx 
                    ON patient_vectors (patient_id)
                """)
            
            logger.info("✅ Vector database 3 connected")
    
    def _get_vector_pool(self, record_number: int):
        """Determine which vector database to use based on record number"""
        if record_number < self.shard_threshold_1:
            return self.vectors_pool1
        elif record_number < self.shard_threshold_2:
            return self.vectors_pool2
        else:
            return self.vectors_pool3
    
    async def upsert_vectors(self, items: List[Dict[str, Any]], start_index: int = 0):
        """
        Insert vectors into appropriate database based on sharding strategy
        
        Args:
            items: List of vector records
            start_index: Starting index for sharding decision
        """
        # Split items between databases
        db1_items = []
        db2_items = []
        db3_items = []
        
        for i, item in enumerate(items):
            record_num = start_index + i
            if record_num < self.shard_threshold_1:
                db1_items.append(item)
            elif record_num < self.shard_threshold_2:
                db2_items.append(item)
            else:
                db3_items.append(item)
        
        # Insert into database 1
        if db1_items and self.vectors_pool1:
            async with self.vectors_pool1.acquire() as conn:
                records = [
                    (item['id'], item['patient_id'], item['vector'], 
                     __import__('json').dumps(item['metadata']))
                    for item in db1_items
                ]
                await conn.executemany("""
                    INSERT INTO patient_vectors (id, patient_id, embedding, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                        patient_id = EXCLUDED.patient_id,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, records)
                logger.info(f"Inserted {len(db1_items)} records into DB1")
        
        # Insert into database 2
        if db2_items and self.vectors_pool2:
            async with self.vectors_pool2.acquire() as conn:
                records = [
                    (item['id'], item['patient_id'], item['vector'], 
                     __import__('json').dumps(item['metadata']))
                    for item in db2_items
                ]
                await conn.executemany("""
                    INSERT INTO patient_vectors (id, patient_id, embedding, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                        patient_id = EXCLUDED.patient_id,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, records)
                logger.info(f"Inserted {len(db2_items)} records into DB2")
        
        # Insert into database 3
        if db3_items and self.vectors_pool3:
            async with self.vectors_pool3.acquire() as conn:
                records = [
                    (item['id'], item['patient_id'], item['vector'], 
                     __import__('json').dumps(item['metadata']))
                    for item in db3_items
                ]
                await conn.executemany("""
                    INSERT INTO patient_vectors (id, patient_id, embedding, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                        patient_id = EXCLUDED.patient_id,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, records)
                logger.info(f"Inserted {len(db3_items)} records into DB3")
    
    async def query_vectors(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        patient_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vectors across both databases and merge results
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            patient_id: Optional patient ID filter
            
        Returns:
            Merged and sorted results from both databases
        """
        import json
        from pgvector.asyncpg import register_vector
        
        results = []
        
        # Query database 1
        if self.vectors_pool1:
            async with self.vectors_pool1.acquire() as conn:
                await register_vector(conn)
                
                if patient_id:
                    rows = await conn.fetch("""
                        SELECT id, patient_id, metadata,
                               1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        WHERE patient_id = $2
                        ORDER BY embedding <=> $1::vector
                        LIMIT $3
                    """, query_vector, patient_id, top_k)
                else:
                    rows = await conn.fetch("""
                        SELECT id, patient_id, metadata,
                               1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                    """, query_vector, top_k)
                
                results.extend([
                    {
                        'id': row['id'],
                        'patient_id': row['patient_id'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'similarity': float(row['similarity'])
                    }
                    for row in rows
                ])
        
        # Query database 2
        if self.vectors_pool2:
            async with self.vectors_pool2.acquire() as conn:
                await register_vector(conn)
                
                if patient_id:
                    rows = await conn.fetch("""
                        SELECT id, patient_id, metadata,
                               1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        WHERE patient_id = $2
                        ORDER BY embedding <=> $1::vector
                        LIMIT $3
                    """, query_vector, patient_id, top_k)
                else:
                    rows = await conn.fetch("""
                        SELECT id, patient_id, metadata,
                               1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                    """, query_vector, top_k)
                
                results.extend([
                    {
                        'id': row['id'],
                        'patient_id': row['patient_id'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'similarity': float(row['similarity'])
                    }
                    for row in rows
                ])
        
        # Query database 3
        if self.vectors_pool3:
            async with self.vectors_pool3.acquire() as conn:
                await register_vector(conn)
                
                if patient_id:
                    rows = await conn.fetch("""
                        SELECT id, patient_id, metadata,
                               1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        WHERE patient_id = $2
                        ORDER BY embedding <=> $1::vector
                        LIMIT $3
                    """, query_vector, patient_id, top_k)
                else:
                    rows = await conn.fetch("""
                        SELECT id, patient_id, metadata,
                               1 - (embedding <=> $1::vector) as similarity
                        FROM patient_vectors
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                    """, query_vector, top_k)
                
                results.extend([
                    {
                        'id': row['id'],
                        'patient_id': row['patient_id'],
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'similarity': float(row['similarity'])
                    }
                    for row in rows
                ])
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all databases"""
        stats = {}
        
        # Auth DB stats
        if self.auth_pool:
            async with self.auth_pool.acquire() as conn:
                user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
                stats['auth_db'] = {
                    'users': user_count,
                    'status': 'connected'
                }
        
        # Vector DB1 stats
        if self.vectors_pool1:
            async with self.vectors_pool1.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM patient_vectors")
                stats['vectors_db1'] = {
                    'records': count,
                    'status': 'connected'
                }
        
        # Vector DB2 stats
        if self.vectors_pool2:
            async with self.vectors_pool2.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM patient_vectors")
                stats['vectors_db2'] = {
                    'records': count,
                    'status': 'connected'
                }
        
        # Vector DB3 stats
        if self.vectors_pool3:
            async with self.vectors_pool3.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM patient_vectors")
                stats['vectors_db3'] = {
                    'records': count,
                    'status': 'connected'
                }
        
        return stats
    
    async def close(self):
        """Close all database connections"""
        if self.auth_pool:
            await self.auth_pool.close()
        if self.vectors_pool1:
            await self.vectors_pool1.close()
        if self.vectors_pool2:
            await self.vectors_pool2.close()
        if self.vectors_pool3:
            await self.vectors_pool3.close()


# Singleton instance
_multi_db_manager = None


async def get_multi_db_manager() -> MultiDatabaseManager:
    """Get or create the multi-database manager"""
    global _multi_db_manager
    
    if _multi_db_manager is None:
        _multi_db_manager = MultiDatabaseManager()
        await _multi_db_manager.initialize()
    
    return _multi_db_manager
