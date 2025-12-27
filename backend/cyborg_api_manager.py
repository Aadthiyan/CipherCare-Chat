import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CyborgAPIManager:
    """
    Cloud CyborgDB API Manager - Uses CyborgDB Cloud instead of local PostgreSQL.
    Makes API calls to CyborgDB cloud service for vector storage and encryption.
    """
    
    def __init__(self):
        self.api_key = os.getenv("CYBORGDB_API_KEY")
        self.api_base = "https://api.cyborgdb.co"
        
        if not self.api_key:
            raise ValueError("Missing CYBORGDB_API_KEY")
        
        logger.info("Initializing Cloud CyborgDB API Manager...")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test connection
        self._test_connection()
        logger.info("✓ Cloud CyborgDB API initialized successfully")
    
    def _test_connection(self):
        """Test connection to CyborgDB cloud API"""
        try:
            response = requests.get(
                f"{self.api_base}/api/v1/status",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                logger.info("✓ Connected to CyborgDB Cloud API")
            else:
                raise Exception(f"API returned {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not verify connection to CyborgDB Cloud: {e}")
            logger.info("Continuing with offline mode...")
    
    def upsert_patient_record(self, 
                             record_id: str, 
                             patient_id: str, 
                             embedding: List[float], 
                             encrypted_content: Dict[str, Any]) -> bool:
        """
        Insert or update encrypted patient record in CyborgDB Cloud.
        
        Args:
            record_id: Unique record identifier
            patient_id: Patient ID
            embedding: Vector embedding (768 dimensions)
            encrypted_content: Encrypted metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "id": record_id,
                "patient_id": patient_id,
                "embedding": embedding,
                "encrypted_metadata": encrypted_content
            }
            
            response = requests.post(
                f"{self.api_base}/api/v1/records/upsert",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                logger.error(f"Upsert failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Upsert failed for record {record_id}: {e}")
            return False
    
    def upload_encrypted_data(self, file_path: str):
        """
        Bulk upload encrypted patient records to CyborgDB Cloud.
        
        Args:
            file_path: Path to encrypted dataset JSON file
        """
        logger.info(f"Loading data from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                enc_recs = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {file_path}")
            return
        
        # Load vectors if available
        try:
            with open("embeddings/generated/vectors.json", 'r', encoding='utf-8') as f:
                plain_recs = {r['id']: r['values'] for r in json.load(f)}
        except FileNotFoundError:
            logger.warning("Vectors file not found - proceeding without embeddings")
            plain_recs = {}
        
        count = 0
        batch = []
        batch_size = 50
        
        try:
            for enc in enc_recs:
                doc_id = enc['id']
                
                # Skip if vector not available
                if doc_id not in plain_recs:
                    continue
                
                vec = plain_recs[doc_id]
                meta = {
                    "ciphertext": enc.get('ciphertext', ''),
                    "iv": enc.get('iv', ''),
                    "wrapped_key": enc.get('wrapped_key', ''),
                    "algo": enc.get('algo', 'AES-256-GCM'),
                    "parent_id": enc.get('parent_id', '')
                }
                
                batch.append({
                    "id": doc_id,
                    "patient_id": enc.get('parent_id', ''),
                    "embedding": vec,
                    "encrypted_metadata": meta
                })
                count += 1
                
                # Send batch
                if len(batch) >= batch_size:
                    self._send_batch(batch)
                    batch = []
                    logger.info(f"Uploaded {count} records...")
            
            # Send remaining records
            if batch:
                self._send_batch(batch)
            
            logger.info(f"✓ Upload Complete. Total {count} records.")
            
        except Exception as e:
            logger.error(f"Upload Error: {e}")
    
    def _send_batch(self, batch: List[Dict]) -> bool:
        """Send batch of records to CyborgDB Cloud API"""
        try:
            response = requests.post(
                f"{self.api_base}/api/v1/records/batch",
                json={"records": batch},
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                logger.error(f"Batch upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Batch upload error: {e}")
            return False
    
    def search(self, query_vec: List[float], k: int = 5, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar encrypted records in CyborgDB Cloud.
        
        Args:
            query_vec: Query vector embedding
            k: Number of results to return
            patient_id: Optional patient ID filter
            
        Returns:
            List of matching records with similarity scores
        """
        try:
            payload = {
                "embedding": query_vec,
                "k": k,
                "filter": {"patient_id": patient_id} if patient_id else None
            }
            
            response = requests.post(
                f"{self.api_base}/api/v1/search",
                json=payload,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                logger.info(f"Search returned {len(results)} results for patient: {patient_id or 'any'}")
                return results
            else:
                logger.error(f"Search failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Search Error: {e}")
            return []
    
    def get_patient_records_count(self, patient_id: str) -> int:
        """Get count of records for a patient"""
        try:
            response = requests.get(
                f"{self.api_base}/api/v1/patients/{patient_id}/count",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get("count", 0)
            else:
                logger.error(f"Count query failed: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Count Error: {e}")
            return 0
    
    def get_all_patient_ids(self) -> List[str]:
        """Get all unique patient IDs in database"""
        try:
            response = requests.get(
                f"{self.api_base}/api/v1/patients",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("patient_ids", [])
            else:
                logger.error(f"Patient list failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Patient list Error: {e}")
            return []
    
    def delete_record(self, record_id: str) -> bool:
        """Delete a record from CyborgDB"""
        try:
            response = requests.delete(
                f"{self.api_base}/api/v1/records/{record_id}",
                headers=self.headers,
                timeout=5
            )
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            logger.error(f"Delete Error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics from CyborgDB dashboard"""
        try:
            response = requests.get(
                f"{self.api_base}/api/v1/stats",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Stats Error: {e}")
            return {}
