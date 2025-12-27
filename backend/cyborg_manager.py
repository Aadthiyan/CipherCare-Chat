import os
import json
import logging
import secrets
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import Vault crypto service
from encryption.vault_crypto_service import get_crypto_service

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CyborgDBManager:
    """
    Encrypted Vector Database Manager using PostgreSQL with pgvector.
    Implements HIPAA-compliant encrypted vector search for patient records.
    """
    
    def __init__(self):
        self.conn_str = os.getenv("CYBORGDB_CONNECTION_STRING")
        self.api_key = os.getenv("CYBORGDB_API_KEY")
        
        if not self.conn_str:
            raise ValueError("Missing CYBORGDB_CONNECTION_STRING")
        if not self.api_key:
            raise ValueError("Missing CYBORGDB_API_KEY")
            
        logger.info("Initializing Database Connection...")
        self.engine = create_engine(self.conn_str)
        self.Session = sessionmaker(bind=self.engine)
        self._ensure_table()
        
        # Initialize Vault Transit Crypto Service (Option B - Enterprise encryption)
        logger.info("Initializing Vault Transit Crypto Service...")
        self.crypto_service = get_crypto_service()
        logger.info("✓ Crypto service initialized successfully")

    def _ensure_table(self):
        """
        Create patient_embeddings table with pgvector extension.
        Stores encrypted vectors and metadata for HIPAA compliance.
        """
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Enhanced schema with better indexing
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS patient_embeddings (
                    id UUID PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    embedding vector(768),
                    encrypted_metadata JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Create indexes for better performance
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_patient_id 
                ON patient_embeddings(patient_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_embedding_cosine 
                ON patient_embeddings 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            conn.commit()
        logger.info("Table patient_embeddings verified.")

    def upsert_patient_record(self, 
                             record_id: str, 
                             patient_id: str, 
                             embedding: List[float], 
                             encrypted_content: Dict[str, Any]) -> bool:
        """
        Insert or update a single encrypted patient record.
        
        Args:
            record_id: Unique identifier for the record
            patient_id: Patient identifier
            embedding: Vector embedding (768 dimensions)
            encrypted_content: Encrypted metadata including ciphertext, IV, etc.
            
        Returns:
            True if successful, False otherwise
        """
        session = self.Session()
        try:
            stmt = text("""
                INSERT INTO patient_embeddings (id, patient_id, embedding, encrypted_metadata)
                VALUES (:id, :pid, :vec, :meta)
                ON CONFLICT (id) DO UPDATE 
                SET embedding = EXCLUDED.embedding, 
                    encrypted_metadata = EXCLUDED.encrypted_metadata,
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            session.execute(stmt, {
                "id": record_id,
                "pid": patient_id,
                "vec": str(embedding),
                "meta": json.dumps(encrypted_content)
            })
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Upsert failed for record {record_id}: {e}")
            return False
        finally:
            session.close()

    def upload_encrypted_data(self, file_path: str):
        """
        Bulk upload encrypted patient records from JSON file.
        Combines plaintext vectors with encrypted metadata.
        """
        logger.info(f"Loading data from {file_path} (Merging Vectors + Ciphertext)")
        
        # Load Plaintext Vectors (Index)
        try:
            with open("embeddings/generated/vectors.json", 'r', encoding='utf-8') as f:
                plain_recs = {r['id']: r['values'] for r in json.load(f)}
        except FileNotFoundError:
             logger.error("Vectors file not found.")
             return

        # Load Encrypted Metadata
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                enc_recs = json.load(f)
        except FileNotFoundError:
             logger.error("Encrypted file not found.")
             return

        session = self.Session()
        count = 0
        try:
            for enc in enc_recs:
                doc_id = enc['id']
                if doc_id not in plain_recs:
                    continue
                
                vec = plain_recs[doc_id]
                meta = {
                    "ciphertext": enc['ciphertext'],
                    "iv": enc['iv'],
                    "wrapped_key": enc['wrapped_key'],
                    "algo": enc['algo'],
                    "parent_id": enc['parent_id']
                }
                
                stmt = text("""
                    INSERT INTO patient_embeddings (id, patient_id, embedding, encrypted_metadata)
                    VALUES (:id, :pid, :vec, :meta)
                    ON CONFLICT (id) DO UPDATE 
                    SET embedding = EXCLUDED.embedding, 
                        encrypted_metadata = EXCLUDED.encrypted_metadata,
                        updated_at = CURRENT_TIMESTAMP
                """)
                
                session.execute(stmt, {
                    "id": doc_id,
                    "pid": enc['parent_id'],
                    "vec": str(vec),
                    "meta": json.dumps(meta)
                })
                count += 1
                
                if count % 50 == 0:
                    session.commit()
                    logger.info(f"Committed {count} records...")
                    
            session.commit()
            logger.info(f"Upload Complete. Total {count} records.")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database Error: {e}")
        finally:
            session.close()

    def search(self, query_vec: List[float], k: int = 5, patient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for similar encrypted patient records using cosine similarity.
        
        Args:
            query_vec: Query vector embedding
            k: Number of results to return
            patient_id: Optional patient ID to filter results
            
        Returns:
            List of matching records with encrypted metadata and similarity scores
        """
        session = self.Session()
        try:
            # Use cosine distance for similarity search
            sql = """
                SELECT id, patient_id, encrypted_metadata, 1 - (embedding <=> :qvec) as similarity
                FROM patient_embeddings
            """
            params = {"qvec": str(query_vec), "k": k}
            
            if patient_id:
                sql += " WHERE patient_id = :pid"
                params["pid"] = patient_id
                
            sql += " ORDER BY embedding <=> :qvec LIMIT :k"
            
            res = session.execute(text(sql), params).fetchall()
            
            # Format results
            results = []
            for row in res:
                results.append({
                    "id": str(row[0]),
                    "patient_id": row[1],
                    "metadata": row[2],  # Encrypted metadata
                    "score": float(row[3])
                })
            
            logger.info(f"Search returned {len(results)} results for patient: {patient_id or 'any'}")
            return results
            
        except Exception as e:
            logger.error(f"Search Failed: {e}")
            return []
        finally:
            session.close()
    
    def get_patient_records_count(self, patient_id: str) -> int:
        """Get the count of records for a specific patient."""
        session = self.Session()
        try:
            result = session.execute(
                text("SELECT COUNT(*) FROM patient_embeddings WHERE patient_id = :pid"),
                {"pid": patient_id}
            ).scalar()
            return result or 0
        except Exception as e:
            logger.error(f"Count query failed: {e}")
            return 0
        finally:
            session.close()
    
    def get_all_patient_ids(self) -> List[str]:
        """Get list of all unique patient IDs in the database."""
        session = self.Session()
        try:
            result = session.execute(
                text("SELECT DISTINCT patient_id FROM patient_embeddings ORDER BY patient_id")
            ).fetchall()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to fetch patient IDs: {e}")
            return []
        finally:
            session.close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    manager = CyborgDBManager()
    
    # Test: Get patient IDs
    print("Patient IDs in database:", manager.get_all_patient_ids())
    
    # Upload (if data exists)
    if os.path.exists("embeddings/encrypted/vectors_enc.json"):
        manager.upload_encrypted_data("embeddings/encrypted/vectors_enc.json")
    
    # Test Query
    if os.path.exists("embeddings/generated/vectors.json"):
        with open("embeddings/generated/vectors.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data:
                v = data[0]['values']
                res = manager.search(v, k=3)
                print("Search Results:", len(res), "records found")
                for r in res:
                    print(f"  - Patient: {r['patient_id']}, Score: {r['score']:.4f}")

