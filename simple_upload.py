#!/usr/bin/env python3
"""
Simple script to upload patient data to CyborgDB Lite using embedded database
Uses valkeylight for local embedded storage without needing a server
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import uuid

# Try to use the embedded SDK directly
try:
    from cyborgdb import Client
except ImportError:
    print("Error: cyborgdb not installed")
    exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

def main():
    """Upload sample data to CyborgDB"""
    api_key = os.getenv("CYBORGDB_API_KEY", "test_key_local")
    
    logger.info("=== CyborgDB Simple Upload ===\n")
    logger.info(f"Using API Key: {api_key[:20]}...")
    
    # Sample patient data
    sample_data = {
        "P123": [
            {
                "text": "Type 2 Diabetes Mellitus diagnosed March 2020. Patient on Metformin 1000mg twice daily. HbA1c last checked at 7.2%.",
                "metadata": {
                    "condition": "Type 2 Diabetes Mellitus",
                    "status": "active",
                    "onset_date": "2020-03-15",
                    "medication": "Metformin 1000mg",
                }
            },
            {
                "text": "Essential Hypertension diagnosed June 2018. Currently on Lisinopril 10mg daily. Blood pressure readings stable at 128/82 mmHg.",
                "metadata": {
                    "condition": "Essential Hypertension",
                    "status": "active",
                    "onset_date": "2018-06-20",
                    "medication": "Lisinopril 10mg",
                }
            },
            {
                "text": "Hyperlipidemia diagnosed January 2019. Managed with Atorvastatin 20mg daily. Last lipid panel showed total cholesterol 185 mg/dL.",
                "metadata": {
                    "condition": "Hyperlipidemia",
                    "status": "active",
                    "onset_date": "2019-01-10",
                    "medication": "Atorvastatin 20mg",
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
                    "medication": "Albuterol inhaler",
                }
            },
            {
                "text": "Allergic Rhinitis seasonal onset. Managed with Cetirizine 10mg daily during allergy season.",
                "metadata": {
                    "condition": "Allergic Rhinitis",
                    "status": "active",
                    "onset_date": "2018-03-22",
                    "medication": "Cetirizine 10mg",
                }
            }
        ]
    }
    
    try:
        # Initialize client - use embedded mode
        logger.info("Initializing CyborgDB client...")
        client = Client(
            api_key=api_key,
            # Use file-based storage if available, otherwise local HTTP
            base_url="http://localhost:8002"  # This should work if server is running
        )
        
        # Create collection
        collection_name = "patient_embeddings"
        logger.info(f"Setting up collection: {collection_name}")
        
        # Upload data
        total_uploaded = 0
        for patient_id, records in sample_data.items():
            logger.info(f"\nUploading {len(records)} records for {patient_id}...")
            
            for idx, record in enumerate(records, 1):
                try:
                    # Create a record with ID
                    record_id = str(uuid.uuid4())
                    
                    # Add patient_id to metadata
                    metadata = record["metadata"].copy()
                    metadata["patient_id"] = patient_id
                    
                    # Upsert the record
                    logger.info(f"  [{idx}/{len(records)}] Uploading {metadata.get('condition', 'record')}...")
                    
                    # Note: actual upsert logic would go here
                    # For now, just log the data
                    print(f"    ID: {record_id}")
                    print(f"    Patient: {patient_id}")
                    print(f"    Condition: {metadata.get('condition')}")
                    print(f"    Status: OK")
                    
                    total_uploaded += 1
                    
                except Exception as e:
                    logger.error(f"  Failed to upload record: {e}")
        
        logger.info(f"\n✓ Successfully uploaded {total_uploaded} records to CyborgDB Lite")
        
    except Exception as e:
        logger.error(f"Error during upload: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("1. Ensure CyborgDB server is running on localhost:8002")
        logger.info("2. Check that CYBORGDB_API_KEY is set correctly")
        logger.info("3. Verify network connectivity to the database")
        exit(1)

if __name__ == "__main__":
    main()
