"""
Unified Vector Database Manager
Supports both CyborgDB (local) and Pinecone (cloud)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class VectorDatabaseManager(ABC):
    """Abstract base class for vector databases"""
    
    @abstractmethod
    def upsert(self, record_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Upload embedding vector"""
        pass
    
    @abstractmethod
    def search(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    def delete(self, record_id: str):
        """Delete a record"""
        pass
    
    @abstractmethod
    def batch_upsert(self, records: List[tuple]):
        """Batch upload embeddings"""
        pass


class PineconeManager(VectorDatabaseManager):
    """Pinecone vector database (free tier: 1 index, 1GB storage)"""
    
    def __init__(self, index_name: str = "patient-embeddings"):
        try:
            import pinecone
            self.pinecone = pinecone
        except ImportError:
            raise ImportError("pinecone not installed. Install with: pip install pinecone")
        
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENV", "gcp-starter")
        
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        logger.info(f"Initializing Pinecone (env: {environment})")
        
        try:
            # Initialize Pinecone (v3+ API)
            self.pc = pinecone.Pinecone(api_key=api_key)
            
            # Get or create index
            self.index_name = index_name
            self.index = self.pc.Index(index_name)
            
            logger.info(f"✓ Pinecone initialized (index: {index_name})")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def upsert(self, record_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Upload single embedding to Pinecone"""
        try:
            self.index.upsert(
                vectors=[(
                    record_id,
                    embedding,
                    metadata
                )]
            )
            logger.debug(f"Upserted record: {record_id}")
        except Exception as e:
            logger.error(f"Failed to upsert to Pinecone: {e}")
            raise
    
    def search(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search Pinecone for similar embeddings"""
        try:
            results = self.index.query(
                embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match.get("metadata", {})
                }
                for match in results.get("matches", [])
            ]
        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            raise
    
    def delete(self, record_id: str):
        """Delete record from Pinecone"""
        try:
            self.index.delete(ids=[record_id])
            logger.debug(f"Deleted record: {record_id}")
        except Exception as e:
            logger.error(f"Failed to delete from Pinecone: {e}")
            raise
    
    def batch_upsert(self, records: List[tuple]):
        """Batch upload to Pinecone
        records: List of (record_id, embedding, metadata) tuples
        """
        try:
            self.index.upsert(vectors=records)
            logger.info(f"Batch upserted {len(records)} records")
        except Exception as e:
            logger.error(f"Failed batch upsert to Pinecone: {e}")
            raise


class CyborgLiteManagerWrapper(VectorDatabaseManager):
    """Wrapper for CyborgDB (for local development)"""
    
    def __init__(self):
        try:
            from backend.cyborg_lite_manager import CyborgLiteManager
            self.manager = CyborgLiteManager()
        except ImportError:
            raise ImportError("CyborgDB not available")
    
    def upsert(self, record_id: str, embedding: List[float], metadata: Dict[str, Any]):
        self.manager.upsert(record_id, embedding, metadata)
    
    def search(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        return self.manager.search(embedding, top_k)
    
    def delete(self, record_id: str):
        # CyborgDB may not have delete, so we handle gracefully
        try:
            self.manager.delete(record_id)
        except:
            logger.warning(f"Delete not supported for record: {record_id}")
    
    def batch_upsert(self, records: List[tuple]):
        # CyborgDB may not have batch_upsert
        for record_id, embedding, metadata in records:
            self.upsert(record_id, embedding, metadata)


def get_vector_db_manager() -> VectorDatabaseManager:
    """Factory function to get appropriate vector database manager"""
    
    db_type = os.getenv("VECTOR_DB_TYPE", "pinecone").lower()
    
    logger.info(f"Using vector database: {db_type}")
    
    if db_type == "pinecone":
        return PineconeManager()
    elif db_type == "cyborgdb":
        return CyborgLiteManagerWrapper()
    else:
        # Default to Pinecone for cloud deployments
        logger.warning(f"Unknown DB type '{db_type}', defaulting to Pinecone")
        return PineconeManager()
