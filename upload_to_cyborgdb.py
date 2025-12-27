#!/usr/bin/env python3
"""
CyborgDB Data Upload Utility
Processes documents and uploads embeddings to CyborgDB cloud
"""

import os
import json
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv
import httpx
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")
CYBORGDB_BASE_URL = "https://api.cyborgdb.co/v1"
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
COLLECTION_NAME = "patient_embeddings"

class CyborgDBUploader:
    def __init__(self):
        if not CYBORGDB_API_KEY:
            raise ValueError("CYBORGDB_API_KEY not found in .env")
        
        self.api_key = CYBORGDB_API_KEY
        self.base_url = CYBORGDB_BASE_URL
        
        # Log API key prefix for debugging (never log full key)
        key_prefix = self.api_key[:20] + "..." if self.api_key else "None"
        logger.info(f"Using API Key: {key_prefix}")
        
        # CyborgDB expects authorization with algorithm name prefix
        # Try Digest authentication with API key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"✓ Initialized with model: {EMBEDDING_MODEL}")
    
    def create_collection(self):
        """Create patient_embeddings collection if it doesn't exist"""
        try:
            # Add API key as query parameter instead of header
            url = f"{self.base_url}/collections?api_key={self.api_key}"
            
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json={
                        "name": COLLECTION_NAME,
                        "description": "Encrypted patient medical records with embeddings",
                        "dimension": 768
                    },
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✓ Collection '{COLLECTION_NAME}' ready")
                    return True
                else:
                    logger.warning(f"Collection creation: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def upload_record(self, patient_id: str, text: str, metadata: dict) -> bool:
        """Upload a single record with embedding to CyborgDB"""
        try:
            # Generate embedding
            vector = self.embedder.encode(text).tolist()
            
            # Create record
            record = {
                "id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "vector": vector,
                "metadata": {
                    "patient_id": patient_id,
                    **metadata
                }
            }
            
            # Add API key as query parameter
            url = f"{self.base_url}/collections/{COLLECTION_NAME}/upsert?api_key={self.api_key}"
            
            # Upload to CyborgDB
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=record,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✓ Uploaded: {metadata.get('condition', 'record')} for {patient_id}")
                    return True
                else:
                    logger.error(f"Upload failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False
    
    def upload_sample_data(self):
        """Upload sample patient data for testing"""
        sample_patients = {
            "P123": [
                {
                    "text": "Type 2 Diabetes Mellitus diagnosed March 2020. Patient on Metformin 1000mg twice daily. HbA1c last checked at 7.2%.",
                    "metadata": {
                        "condition": "Type 2 Diabetes Mellitus",
                        "status": "active",
                        "onset_date": "2020-03-15",
                        "icd_code": "E11.9",
                        "type": "condition",
                        "medication": "Metformin 1000mg BID"
                    }
                },
                {
                    "text": "Essential Hypertension diagnosed June 2018. On Lisinopril 10mg daily. Blood pressure control adequate at 140/85.",
                    "metadata": {
                        "condition": "Essential Hypertension",
                        "status": "active",
                        "onset_date": "2018-06-20",
                        "icd_code": "I10",
                        "type": "condition",
                        "medication": "Lisinopril 10mg daily"
                    }
                },
                {
                    "text": "Hyperlipidemia diagnosed January 2019. Patient on Atorvastatin 20mg daily. LDL last checked at 95 mg/dL.",
                    "metadata": {
                        "condition": "Hyperlipidemia",
                        "status": "active",
                        "onset_date": "2019-01-10",
                        "icd_code": "E78.5",
                        "type": "condition",
                        "medication": "Atorvastatin 20mg daily"
                    }
                }
            ],
            "P456": [
                {
                    "text": "Asthma diagnosed age 12. Currently well-controlled on Albuterol inhaler PRN. Last exacerbation was 6 months ago.",
                    "metadata": {
                        "condition": "Asthma",
                        "status": "active",
                        "onset_date": "2012-06-01",
                        "icd_code": "J45.9",
                        "type": "condition",
                        "medication": "Albuterol inhaler PRN"
                    }
                },
                {
                    "text": "Allergic Rhinitis diagnosed age 18. Treated with Cetirizine 10mg daily as needed. Seasonal symptoms.",
                    "metadata": {
                        "condition": "Allergic Rhinitis",
                        "status": "active",
                        "onset_date": "2016-03-15",
                        "icd_code": "J30.9",
                        "type": "condition",
                        "medication": "Cetirizine 10mg PRN"
                    }
                }
            ]
        }
        
        logger.info(f"Uploading {sum(len(v) for v in sample_patients.values())} sample records...")
        
        success_count = 0
        for patient_id, records in sample_patients.items():
            for record in records:
                if self.upload_record(patient_id, record["text"], record["metadata"]):
                    success_count += 1
        
        logger.info(f"✓ Successfully uploaded {success_count} records")
        return success_count

def main():
    """Main upload workflow"""
    logger.info("=== CyborgDB Data Upload Utility ===\n")
    
    uploader = CyborgDBUploader()
    
    # Create collection
    logger.info("Step 1: Preparing collection...")
    if not uploader.create_collection():
        logger.warning("Collection may already exist, continuing...")
    
    # Upload sample data
    logger.info("\nStep 2: Uploading sample patient data...")
    uploader.upload_sample_data()
    
    logger.info("\n✓ Upload complete! Check CyborgDB dashboard for records.")
    logger.info("  Query endpoint will now use real data instead of fallback samples.")

if __name__ == "__main__":
    main()
