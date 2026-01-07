"""
Pre-load patient data into CyborgDB during Docker build
This script runs ONCE during image build, baking data into the image
"""

import os
import json
import hashlib
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Configuration
CYBORGDB_URL = "http://localhost:8002"
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY", "cyborg_9e8c1c2e25c944d78f41ac7f23376d23")
DATA_FILE = "/app/data/synthea_structured_cipercare.json"
INDEX_NAME = "patient_records_v1"
LIMIT = 76317  # 150 patients

print("=" * 70)
print("🚀 Pre-loading Patient Data into CyborgDB")
print("=" * 70)
print(f"\nData file: {DATA_FILE}")
print(f"Target: {CYBORGDB_URL}")
print(f"Index: {INDEX_NAME}")
print(f"Limit: {LIMIT} records (150 patients)")

try:
    # Wait for CyborgDB to be ready
    print("\n⏳ Waiting for CyborgDB to start...")
    time.sleep(5)
    
    # Initialize CyborgDB client
    import cyborgdb
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    print("✓ Connected to CyborgDB")
    
    # Load embedding model
    print("\n📥 Loading embedding model...")
    embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
    print("✓ Model loaded")
    
    # Load patient data
    print(f"\n📂 Loading patient data from {DATA_FILE}...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    if LIMIT:
        records = records[:LIMIT]
    
    print(f"✓ Loaded {len(records)} records")
    
    # Count patients
    patients = set(r.get('patient_id') for r in records)
    print(f"✓ Found {len(patients)} unique patients")
    
    # Create index
    print(f"\n📊 Creating index: {INDEX_NAME}...")
    combined = f"{CYBORGDB_API_KEY}:{INDEX_NAME}"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    try:
        index = client.create_index(
            index_name=INDEX_NAME,
            index_key=index_key
        )
        print(f"✓ Created index '{INDEX_NAME}'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"ℹ️  Index already exists, loading...")
            index = client.load_index(
                index_name=INDEX_NAME,
                index_key=index_key
            )
            print(f"✓ Loaded index '{INDEX_NAME}'")
        else:
            raise
    
    # Create embeddings in batches
    print(f"\n🔄 Creating embeddings for {len(records)} records...")
    batch_size = 256
    all_embeddings = []
    
    # Prepare texts
    texts = []
    for record in records:
        text = record.get('text_for_embedding') or record.get('text_summary', '')
        if not text:
            parts = []
            if 'effective_date' in record:
                parts.append(record['effective_date'])
            if 'display' in record:
                parts.append(record['display'])
            text = ': '.join(str(p) for p in parts if p) or "Unknown record"
        texts.append(text)
    
    # Generate embeddings in batches
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_embeddings = embedder.encode(batch_texts, show_progress_bar=False)
        all_embeddings.extend(batch_embeddings.tolist())
        
        if (i // batch_size) % 10 == 0:
            print(f"  Progress: {i}/{len(texts)} embeddings created...")
    
    print(f"✓ Created {len(all_embeddings)} embeddings")
    
    # Assign embeddings to records
    for i, record in enumerate(records):
        record['embedding'] = all_embeddings[i]
    
    # Upload to CyborgDB in batches
    print(f"\n📤 Uploading {len(records)} records to CyborgDB...")
    upload_batch_size = 100
    success_count = 0
    error_count = 0
    
    for i in range(0, len(records), upload_batch_size):
        batch = records[i:i+upload_batch_size]
        
        try:
            items = []
            for record in batch:
                items.append({
                    "id": str(record.get('record_id', f"record_{i}")),
                    "vector": record.get('embedding'),
                    "metadata": {
                        "patient_id": record.get('patient_id'),
                        "record_type": record.get('record_type'),
                        "text_summary": record.get('text_summary', ''),
                        "display": record.get('display', ''),
                        "effective_date": record.get('effective_date', ''),
                        "status": record.get('status', 'final')
                    }
                })
            
            index.upsert(items)
            success_count += len(batch)
            
            if (i // upload_batch_size) % 10 == 0:
                print(f"  Progress: {success_count}/{len(records)} records uploaded...")
            
            time.sleep(0.02)
            
        except Exception as e:
            error_count += len(batch)
            print(f"  ⚠️  Batch error: {str(e)[:100]}")
    
    print(f"\n✅ Upload complete!")
    print(f"   Success: {success_count}")
    print(f"   Errors: {error_count}")
    
    if success_count == len(records):
        print(f"\n🎉 SUCCESS! All {len(records)} records loaded into CyborgDB!")
        print(f"   Patients: {len(patients)}")
        print(f"   Index: {INDEX_NAME}")
        print(f"\n✅ Data is now baked into the Docker image!")
        exit(0)
    else:
        print(f"\n⚠️  WARNING: Only {success_count}/{len(records)} records loaded")
        exit(1)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
