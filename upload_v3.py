"""
Fast Upload to patient_data_v3 (Fresh Start)
"""

import csv
import sys
import time
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()

# Increase CSV field limit
csv.field_size_limit(sys.maxsize)

def upload_v3():
    print("="*70)
    print("FRESH UPLOAD TO PATIENT_DATA_V3")
    print("="*70)
    
    # Load fast CSV
    input_file = "synthea_structured.csv"
    records = []
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        # Take 1500 records to be safe (contains PID-101 and more)
        records = all_rows[:1500]

    print(f"Loaded {len(records)} records for upload.")
    
    # Initialize
    print("\nInitializing...")
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    db = CyborgLiteManager()
    collection = "patient_data_v3"
    
    # Embeddings
    print("\nGenerating embeddings...")
    start_time = time.time()
    texts = [r.get('text_summary', '') for r in records]
    embeddings = embedder.encode(texts, show_progress_bar=True)
    print(f"✓ Embeddings done in {time.time()-start_time:.1f}s")
    
    # Upload loop
    print("\nUploading to CyborgDB (with cached index)...")
    start_time = time.time()
    success = 0
    errors = 0
    
    # Batch thinking, but one-by-one upsert is fine now with caching
    for i, (record, embedding) in enumerate(zip(records, embeddings)):
        try:
            # Clean metadata (remove huge text fields if needed)
            meta = {k:v for k,v in record.items() if k != 'embedding'}
            
            db.upsert(
                record_id=record.get('record_id', f'rec-{i}'),
                patient_id=record.get('patient_id', 'unknown'),
                embedding=embedding.tolist(),
                metadata=meta,
                collection=collection
            )
            success += 1
            if i % 100 == 0:
                print(f"  {i}/{len(records)} uploaded...")
                
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"Error: {e}")

    total_time = time.time() - start_time
    print("\n" + "="*70)
    print("✓ UPLOAD COMPLETE")
    print(f"uploaded: {success}")
    print(f"errors: {errors}")
    print(f"time: {total_time:.1f}s")
    print("="*70)

if __name__ == "__main__":
    upload_v3()
