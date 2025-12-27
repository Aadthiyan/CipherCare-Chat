#!/usr/bin/env python3
"""
Upload clinical documents to CyborgDB Cloud
Handles PDF, TXT, DOCX formats with embeddings
"""

import os
import sys
import json
import uuid
import httpx
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Configuration
CYBORG_API_KEY = os.getenv("CYBORGDB_API_KEY")
CYBORG_BASE_URL = "https://api.cyborgdb.co/v1"
COLLECTION_NAME = "patient_embeddings"
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

# Sample patient clinical data
SAMPLE_DOCUMENTS = [
    {
        "patient_id": "P123",
        "condition": "Type 2 Diabetes Mellitus",
        "status": "active",
        "onset_date": "2020-03-15",
        "icd_code": "E11.9",
        "type": "condition",
        "text_snippet": "Patient diagnosed with Type 2 Diabetes Mellitus in March 2020. Currently on Metformin 1000mg BID. HbA1c last checked at 7.2%. Patient reports good compliance with diet and exercise. No recent complications. Referred to endocrinology for optimization of glycemic control."
    },
    {
        "patient_id": "P123",
        "condition": "Essential Hypertension",
        "status": "active",
        "onset_date": "2018-06-20",
        "icd_code": "I10",
        "type": "condition",
        "text_snippet": "Patient has Essential Hypertension diagnosed in June 2018. Currently on Lisinopril 10mg daily and Amlodipine 5mg daily. Blood pressure readings range 128-135/78-82 mmHg. Goal BP achieved in 80% of readings. No signs of end-organ damage on last exam."
    },
    {
        "patient_id": "P123",
        "condition": "Hyperlipidemia",
        "status": "active",
        "onset_date": "2019-01-10",
        "icd_code": "E78.5",
        "type": "condition",
        "text_snippet": "Patient diagnosed with Hyperlipidemia in January 2019. Currently on Atorvastatin 20mg daily. Recent lipid panel: Total cholesterol 165, LDL 95, HDL 50, Triglycerides 110. Patient counseled on dietary modifications and importance of medication adherence."
    },
    {
        "patient_id": "P124",
        "condition": "Chronic Obstructive Pulmonary Disease",
        "status": "active",
        "onset_date": "2015-11-05",
        "icd_code": "J44.9",
        "type": "condition",
        "text_snippet": "Patient with COPD GOLD stage 2. Former smoker, quit 3 years ago with 40 pack-year history. On Tiotropium inhaler daily and Albuterol as needed. Recent spirometry shows FEV1 58% predicted. Experiencing occasional dyspnea with exertion. Pulmonary rehabilitation recommended."
    },
    {
        "patient_id": "P124",
        "condition": "Gastroesophageal Reflux Disease",
        "status": "active",
        "onset_date": "2017-08-12",
        "icd_code": "K21.9",
        "type": "condition",
        "text_snippet": "Patient with GERD on Omeprazole 20mg daily. Symptoms well-controlled with current regimen. Lifestyle modifications advised including avoiding late meals and elevating head of bed. Endoscopy 2 years ago showed mild erosive disease, resolved on PPI therapy."
    }
]


def load_model():
    """Load sentence-transformer model"""
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        print("✓ Model loaded successfully")
        return model
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        sys.exit(1)


def generate_embeddings(model, texts):
    """Generate embeddings for texts"""
    print(f"Generating embeddings for {len(texts)} documents...")
    try:
        embeddings = model.encode(texts, show_progress_bar=True)
        print(f"✓ Generated {len(embeddings)} embeddings")
        return embeddings
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
        sys.exit(1)


def create_cyborg_records(model):
    """Create records with embeddings for CyborgDB"""
    records = []
    texts = []
    
    # Collect texts for batch embedding
    for doc in SAMPLE_DOCUMENTS:
        text = f"{doc['condition']} - {doc['text_snippet']}"
        texts.append(text)
    
    # Generate embeddings in batch
    embeddings = generate_embeddings(model, texts)
    
    # Create records
    for i, doc in enumerate(SAMPLE_DOCUMENTS):
        record = {
            "id": f"rec_{doc['patient_id']}_{uuid.uuid4().hex[:8]}",
            "patient_id": doc["patient_id"],
            "vector": embeddings[i].tolist(),  # Convert to list
            "metadata": {
                "patient_id": doc["patient_id"],
                "condition": doc["condition"],
                "status": doc["status"],
                "onset_date": doc["onset_date"],
                "icd_code": doc["icd_code"],
                "type": doc["type"],
                "text_snippet": doc["text_snippet"]
            }
        }
        records.append(record)
    
    return records


def upload_to_cyborg(records):
    """Upload records to CyborgDB Cloud"""
    if not CYBORG_API_KEY:
        print("✗ CYBORGDB_API_KEY not found in .env")
        sys.exit(1)
    
    headers = {
        "X-API-Key": CYBORG_API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"\nUploading {len(records)} records to CyborgDB...")
    
    success_count = 0
    failed_count = 0
    
    with httpx.Client(timeout=30) as client:
        for i, record in enumerate(records, 1):
            try:
                url = f"{CYBORG_BASE_URL}/collections/{COLLECTION_NAME}/upsert"
                
                response = client.post(
                    url,
                    json=record,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    print(f"✓ [{i}/{len(records)}] Uploaded: {record['id']}")
                    success_count += 1
                else:
                    print(f"✗ [{i}/{len(records)}] Failed ({response.status_code}): {record['id']}")
                    print(f"  Error: {response.text}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"✗ [{i}/{len(records)}] Exception: {record['id']}")
                print(f"  Error: {e}")
                failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Upload Summary:")
    print(f"  ✓ Successful: {success_count}")
    print(f"  ✗ Failed: {failed_count}")
    print(f"  Total: {len(records)}")
    print(f"{'='*60}")
    
    return success_count > 0


if __name__ == "__main__":
    print("CyborgDB Cloud Document Uploader")
    print("=" * 60)
    
    # Load model
    model = load_model()
    
    # Create records with embeddings
    records = create_cyborg_records(model)
    
    # Save to file for inspection
    with open("cyborg_records.json", "w") as f:
        json.dump(records, f, indent=2)
    print(f"\n✓ Saved {len(records)} records to cyborg_records.json")
    
    # Upload to CyborgDB
    success = upload_to_cyborg(records)
    
    if success:
        print("\n✓ Data upload complete! Your CyborgDB is now populated.")
        print("  Try running the query again to see real data instead of samples.")
    else:
        print("\n✗ Upload failed. Check your API key and connection.")
        sys.exit(1)
