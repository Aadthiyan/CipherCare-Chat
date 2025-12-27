#!/usr/bin/env python3
"""
CyborgDB Data Upload Utility - Using Embedded SDK
Uploads embeddings to the local CyborgDB Lite instance
"""

import os
import json
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
COLLECTION_NAME = "patient_embeddings"

class CyborgUploadUtility:
    def __init__(self):
        """Initialize uploader with embedder and CyborgDB manager"""
        logger.info("=== CyborgDB Lite Upload Utility ===\n")
        
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Initialized with model: {EMBEDDING_MODEL}")
        
        self.manager = CyborgLiteManager()
        logger.info("CyborgDB Lite manager initialized\n")
    
    def upload_record(self, patient_id: str, text: str, metadata: dict) -> bool:
        """Upload a single record with embedding"""
        try:
            # Generate embedding
            vector = self.embedder.encode(text).tolist()
            
            # Generate record ID
            record_id = str(uuid.uuid4())
            
            # Upsert to database
            success = self.manager.upsert(
                record_id=record_id,
                patient_id=patient_id,
                embedding=vector,
                metadata=metadata,
                collection=COLLECTION_NAME
            )
            
            if success:
                logger.info(f"Uploaded: {metadata.get('condition', 'record')} for {patient_id}")
            return success
                    
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False
    
    def upload_sample_data(self):
        """Upload sample patient data"""
        sample_patients = {
            "P123": [
                {
                    "text": "Type 2 Diabetes Mellitus diagnosed March 2020. Patient on Metformin 1000mg twice daily. HbA1c last checked at 7.2%.",
                    "metadata": {
                        "condition": "Type 2 Diabetes Mellitus",
                        "status": "active",
                        "onset_date": "2020-03-15",
                        "icd_code": "E11.9",
                        "medication": "Metformin 1000mg",
                        "last_hba1c": "7.2%"
                    }
                },
                {
                    "text": "Essential Hypertension diagnosed June 2018. Currently on Lisinopril 10mg daily. Blood pressure readings stable at 128/82 mmHg.",
                    "metadata": {
                        "condition": "Essential Hypertension",
                        "status": "active",
                        "onset_date": "2018-06-20",
                        "icd_code": "I10",
                        "medication": "Lisinopril 10mg",
                        "last_bp": "128/82"
                    }
                },
                {
                    "text": "Hyperlipidemia diagnosed January 2019. Managed with Atorvastatin 20mg daily. Last lipid panel showed total cholesterol 185 mg/dL.",
                    "metadata": {
                        "condition": "Hyperlipidemia",
                        "status": "active",
                        "onset_date": "2019-01-10",
                        "icd_code": "E78.5",
                        "medication": "Atorvastatin 20mg",
                        "last_cholesterol": "185 mg/dL"
                    }
                }
            ],
            "P456": [
                {
                    "text": "Asthma diagnosed 2015. Well-controlled with Albuterol inhaler as needed. No recent exacerbations in past 6 months.",
                    "metadata": {
                        "condition": "Asthma",
                        "status": "active",
                        "onset_date": "2015-05-12",
                        "icd_code": "J45.9",
                        "medication": "Albuterol inhaler",
                        "severity": "mild"
                    }
                },
                {
                    "text": "Allergic Rhinitis seasonal onset. Managed with Cetirizine 10mg daily during allergy season.",
                    "metadata": {
                        "condition": "Allergic Rhinitis",
                        "status": "active",
                        "onset_date": "2018-03-22",
                        "icd_code": "J30.9",
                        "medication": "Cetirizine 10mg",
                        "trigger": "seasonal"
                    }
                }
            ]
        }
        
        logger.info("Step 2: Uploading sample patient data...")
        total_uploaded = 0
        
        for patient_id, records in sample_patients.items():
            logger.info(f"Uploading {len(records)} records for {patient_id}...")
            for record in records:
                if self.upload_record(patient_id, record["text"], record["metadata"]):
                    total_uploaded += 1
        
        logger.info(f"\nSuccessfully uploaded {total_uploaded} records to CyborgDB Lite")
        logger.info("Data is now available for medical queries via LLM\n")


def main():
    """Main entry point"""
    try:
        uploader = CyborgUploadUtility()
        uploader.upload_sample_data()
        
        logger.info("Upload complete!")
        logger.info("Query endpoint will now use real data from CyborgDB Lite")
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
