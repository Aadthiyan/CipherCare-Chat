"""
CyborgDB Lite Manager - Embedded SDK Implementation
Uses the cyborgdb Python SDK directly, not HTTP cloud API
"""

import os
import json
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional
from functools import wraps
import cyborgdb
from backend.exceptions import (
    ServiceInitializationError,
    SearchError,
    DatabaseError,
    ConnectionError as ConnectionErrorException,
    TimeoutError as TimeoutErrorException
)

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries=3, base_delay=1.0, backoff_factor=2.0):
    """Decorator for retrying operations with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    logger.warning(
                        f"Attempt {retries} failed for {func.__name__}: {str(e)[:100]}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

class CyborgLiteManager:
    """
    CyborgDB Lite Manager - Uses embedded SDK for local vector storage
    Compatible with the working implementation from the other project
    """
    
    _client = None
    _index_keys = {}  # Cache for computed keys
    _index_cache = {}  # Cache for loaded indexes - PREVENTS RECREATION!
    
    def __init__(self):
        """Initialize CyborgDB Embedded client (no external service needed)"""
        api_key = os.getenv("CYBORGDB_API_KEY")
        
        if not api_key:
            raise ServiceInitializationError(
                "CyborgDB",
                "Missing CYBORGDB_API_KEY environment variable",
                details={"required_vars": ["CYBORGDB_API_KEY"]}
            )
        
        # Get data directory for persistent storage
        data_dir = os.getenv("CYBORGDB_DATA_DIR", "/app/cyborgdb_data")
        os.makedirs(data_dir, exist_ok=True)
        
        logger.info(f"Initializing CyborgDB Embedded (local storage at {data_dir})")
        
        try:
            # Initialize the embedded CyborgDB client (only once)
            # NO base_url = embedded mode with local file storage!
            if CyborgLiteManager._client is None:
                CyborgLiteManager._client = cyborgdb.Client(
                    api_key=api_key
                    # No base_url = embedded mode!
                )
                logger.info("CyborgDB Embedded client initialized successfully")
        except ConnectionError as e:
            raise ServiceInitializationError(
                "CyborgDB",
                f"Connection refused to {base_url}. Make sure CyborgDB is running.",
                details={"base_url": base_url, "error": str(e)[:100]}
            )
        except Exception as e:
            raise ServiceInitializationError(
                "CyborgDB",
                str(e),
                details={"base_url": base_url, "error_type": type(e).__name__}
            )
    
    @classmethod
    def _get_deterministic_key(cls, index_name: str) -> bytes:
        """Get a deterministic encryption key for an index"""
        api_key = os.getenv("CYBORGDB_API_KEY", "default")
        combined = f"{api_key}:{index_name}"
        return hashlib.sha256(combined.encode()).digest()
    
    @classmethod
    def get_index(cls, index_name: str = "patient_records_v1") -> Any:
        """Get or create an index with encryption"""
        if not cls._client:
            raise ServiceInitializationError(
                "CyborgDB",
                "Client not initialized",
                details={"attempted_index": index_name}
            )
        
        # CHECK CACHE FIRST - This prevents the error loop!
        if index_name in cls._index_cache:
            logger.debug(f"Using cached index '{index_name}'")
            return cls._index_cache[index_name]
        
        try:
            # Get the deterministic key
            index_key = cls._get_deterministic_key(index_name)
            
            # Try to create the index first (will fail if exists, which is ok)
            try:
                index = cls._client.create_index(
                    index_name=index_name,
                    index_key=index_key
                )
                logger.debug(f"Created new index '{index_name}'")
                # CACHE IT!
                cls._index_cache[index_name] = index
                return index
            except Exception as create_error:
                # Check if error is "index already exists" - this is expected and OK
                error_msg = str(create_error).lower()
                if "already exists" in error_msg or "index name" in error_msg:
                    logger.debug(f"Index '{index_name}' already exists, loading it...")
                else:
                    logger.debug(f"Index creation attempt failed for '{index_name}': {str(create_error)[:100]}")
                
                # Try loading the existing index
                try:
                    index = cls._client.load_index(
                        index_name=index_name,
                        index_key=index_key
                    )
                    logger.debug(f"Successfully loaded existing index '{index_name}'")
                    # CACHE IT!
                    cls._index_cache[index_name] = index
                    return index
                except Exception as load_error:
                    # If both creation and loading fail
                    logger.error(f"Failed to both create and load index '{index_name}'")
                    raise DatabaseError(
                        operation=f"get_index({index_name})",
                        reason="Could not create or load index",
                        details={
                            "index_name": index_name,
                            "create_error": str(create_error)[:80],
                            "load_error": str(load_error)[:80]
                        }
                    )
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(
                operation=f"get_index({index_name})",
                reason=str(e),
                details={
                    "index_name": index_name,
                    "error_type": type(e).__name__
                }
            )
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def search(self,
               query_vec: List[float],
               k: int = 5,
               patient_id: Optional[str] = None,
               collection: str = "patient_records_v1") -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the embedded database with retry logic
        
        Args:
            query_vec: Query embedding vector
            k: Number of results
            patient_id: Optional patient filter
            collection: Collection/index name
            
        Returns:
            List of matching records
            
        Raises:
            SearchError: If search operation fails
        """
        if not query_vec:
            raise SearchError(
                "Query vector is empty or None",
                patient_id=patient_id,
                details={"collection": collection}
            )
        
        try:
            index = self.get_index(collection)
            
            # If filtering by patient_id, fetch more results since we filter post-query
            # CyborgDB doesn't support metadata filtering in the query itself
            fetch_k = min(k * 500, 50000) if patient_id else k  # Fetch up to 50k when filtering
            
            # Query the index - returns LIST of dicts with 'id', 'distance', 'metadata'
            results = index.query(query_vectors=[query_vec], top_k=fetch_k)
            
            # Format results
            formatted_results = []
            if results and isinstance(results, list):
                for i, item in enumerate(results):
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dict result {i}: {type(item)}")
                        continue
                    
                    try:
                        # Filter by patient_id if specified
                        item_patient_id = item.get("metadata", {}).get("patient_id")
                        if patient_id and item_patient_id != patient_id:
                            continue
                        
                        formatted_results.append({
                            "id": item.get("id", "unknown"),
                            "patient_id": item_patient_id or patient_id,
                            "metadata": item.get("metadata", {}),
                            "score": item.get("distance", 0)
                        })
                        
                        # Stop once we have enough results for this patient
                        if patient_id and len(formatted_results) >= k:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Failed to process result {i}: {str(e)[:80]}")
                        continue
            
            logger.info(f"Search returned {len(formatted_results)} results for {collection}")
            return formatted_results
            
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Search failed in {collection}: {str(e)[:100]}")
            raise SearchError(
                str(e),
                patient_id=patient_id,
                details={
                    "collection": collection,
                    "k": k,
                    "error_type": type(e).__name__
                }
            )
    
    @retry_with_backoff(max_retries=3, base_delay=0.5)
    def upsert(self,
               record_id: str,
               patient_id: str,
               embedding: List[float],
               metadata: Dict[str, Any],
               collection: str = "patient_data_v2") -> bool:
        """
        Upsert a record with embedding with retry logic
        
        Args:
            record_id: Unique record ID
            patient_id: Patient identifier
            embedding: Vector embedding
            metadata: Record metadata
            collection: Collection name
            
        Returns:
            Success status
            
        Raises:
            DatabaseError: If upsert operation fails
        """
        try:
            if not record_id or not patient_id:
                raise ValueError("record_id and patient_id are required")
            
            if not embedding or len(embedding) == 0:
                raise ValueError("embedding cannot be empty")
            
            index = self.get_index(collection)
            
            # Prepare item in format expected by SDK
            item = {
                "id": str(record_id),
                "vector": embedding,
                "metadata": {
                    "patient_id": patient_id,
                    **metadata
                }
            }
            
            # Upsert to index
            index.upsert([item])
            
            logger.info(f"Upserted record {record_id} for {patient_id} in {collection}")
            return True
            
        except ValueError as e:
            logger.error(f"Validation error in upsert for {record_id}: {e}")
            raise DatabaseError(
                "upsert",
                str(e),
                details={"record_id": record_id, "patient_id": patient_id}
            )
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Upsert failed for {record_id}: {str(e)[:100]}")
            raise DatabaseError(
                "upsert",
                str(e),
                details={
                    "record_id": record_id,
                    "patient_id": patient_id,
                    "error_type": type(e).__name__
                }
            )
    
    @retry_with_backoff(max_retries=3, base_delay=0.5)
    def batch_upsert(self,
                     records: List[Dict[str, Any]],
                     collection: str = "patient_data_v2") -> int:
        """
        Batch upsert multiple records with retry logic
        
        Args:
            records: List of records with id, vector, metadata
            collection: Collection name
            
        Returns:
            Number of successfully upserted records
            
        Raises:
            DatabaseError: If batch operation fails
        """
        if not records:
            logger.warning("batch_upsert called with empty records list")
            return 0
        
        try:
            index = self.get_index(collection)
            
            # Prepare items in format expected by SDK
            items = []
            for i, record in enumerate(records):
                try:
                    if not record.get("id") or not record.get("vector"):
                        logger.warning(f"Skipping record {i} - missing id or vector")
                        continue
                    
                    items.append({
                        "id": str(record.get("id")),
                        "vector": record.get("vector"),
                        "metadata": record.get("metadata", {})
                    })
                except Exception as e:
                    logger.warning(f"Failed to prepare record {i}: {str(e)[:80]}")
                    continue
            
            if not items:
                logger.warning("No valid items to upsert after preparation")
                return 0
            
            # Batch upsert
            index.upsert(items)
            
            logger.info(f"Batch upserted {len(items)} records to {collection}")
            return len(items)
            
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Batch upsert failed in {collection}: {str(e)[:100]}")
            raise DatabaseError(
                "batch_upsert",
                str(e),
                details={
                    "collection": collection,
                    "records_count": len(records),
                    "error_type": type(e).__name__
                }
            )
    
    def get_patient_records_count(self, patient_id: str, collection: str = "patient_data_v2") -> int:
        """Get count of records for a patient"""
        try:
            logger.info(f"Getting record count for {patient_id}")
            index = self.get_index(collection)

            # Use a wide top_k sample to enumerate stored items and filter by metadata
            # Note: this is a best-effort approach for the lite client that lacks a metadata query API
            top_k = 20000
            zero_embedding = [0.0] * 768
            try:
                results = index.query(query_vectors=[zero_embedding], top_k=top_k)
            except Exception as e:
                logger.warning(f"Index query for record count failed: {e}")
                return 0

            count = 0
            if results and isinstance(results, list):
                for item in results:
                    try:
                        meta = item.get("metadata", {})
                        if meta.get("patient_id") == patient_id:
                            count += 1
                    except Exception:
                        continue

            logger.info(f"Found {count} records for {patient_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to get patient record count: {e}")
            return 0
    
    def get_all_patient_ids(self, collection: str = "patient_data_v2") -> List[str]:
        """Get list of all unique patient IDs"""
        try:
            logger.info("Getting all patient IDs")
            index = self.get_index(collection)

            top_k = 20000
            zero_embedding = [0.0] * 768
            try:
                results = index.query(query_vectors=[zero_embedding], top_k=top_k)
            except Exception as e:
                logger.warning(f"Index query for patient ids failed: {e}")
                return []

            ids = set()
            if results and isinstance(results, list):
                for item in results:
                    try:
                        pid = item.get("metadata", {}).get("patient_id")
                        if pid:
                            ids.add(pid)
                    except Exception:
                        continue

            pid_list = sorted(ids)
            logger.info(f"Found {len(pid_list)} unique patient ids")
            return pid_list
        except Exception as e:
            logger.error(f"Failed to get patient IDs: {e}")
            return []


def get_cyborg_manager() -> CyborgLiteManager:
    """Factory function to get CyborgDB manager instance"""
    manager = CyborgLiteManager()
    return manager
