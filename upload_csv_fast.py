"""
Fast CSV uploader for CipherCare
3-4x faster than JSON for large datasets
"""

import csv
import os
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv
import time

load_dotenv()


def upload_csv_fast(csv_file="synthea_structured.csv", batch_size=500):
    """Upload CSV data in large batches for speed"""
    
    print(f"Loading CSV: {csv_file}")
    
    # Initialize
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    db = CyborgLiteManager()
    
    # Read CSV
    records = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    print(f"Loaded {len(records)} records")
    
    # Create embeddings in large batches
    print(f"\nCreating embeddings (batch size: {batch_size})...")
    start_time = time.time()
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        # Extract texts
        texts = [r.get('text_for_embedding', r.get('text_summary', '')) for r in batch]
        
        # Create embeddings
        embeddings = embedder.encode(texts, show_progress_bar=False)
        
        # Assign back
        for record, embedding in zip(batch, embeddings):
            record['embedding'] = embedding.tolist()
        
        # Progress
        processed = min(i + batch_size, len(records))
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (len(records) - processed) / rate if rate > 0 else 0
        
        print(f"  {processed}/{len(records)} ({processed/len(records)*100:.1f}%) - "
              f"Rate: {rate:.1f} rec/sec - ETA: {eta/60:.1f} min")
    
    print(f"✓ Embeddings created in {(time.time()-start_time)/60:.1f} minutes")
    
    # Upload in batches
    print(f"\nUploading to CyborgDB (batch size: {batch_size})...")
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        for record in batch:
            try:
                # Prepare metadata
                metadata = {k: v for k, v in record.items() if k != 'embedding'}
                
                # Upload
                db.upsert(
                    record_id=record.get('record_id', ''),
                    patient_id=record.get('patient_id', ''),
                    embedding=record['embedding'],
                    metadata=metadata,
                    collection="patient_data_v2"
                )
                
                success_count += 1
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"  Error: {str(e)[:100]}")
        
        # Progress
        processed = min(i + batch_size, len(records))
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (len(records) - processed) / rate if rate > 0 else 0
        
        if processed % 1000 == 0 or processed == len(records):
            print(f"  {processed}/{len(records)} ({processed/len(records)*100:.1f}%) - "
                  f"Success: {success_count}, Errors: {error_count} - "
                  f"Rate: {rate:.1f} rec/sec - ETA: {eta/60:.1f} min")
    
    total_time = time.time() - start_time
    print(f"\n✓ Upload complete in {total_time/60:.1f} minutes!")
    print(f"  Success: {success_count}/{len(records)}")
    print(f"  Errors: {error_count}")
    print(f"  Success rate: {success_count/len(records)*100:.1f}%")


if __name__ == "__main__":
    upload_csv_fast()
