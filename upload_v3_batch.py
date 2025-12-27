"""
FAST Batch Upload to patient_data_v3
Uses direct index.upsert(batch) for maximum speed.
"""

import csv
import sys
import time
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()
csv.field_size_limit(sys.maxsize)

def upload_v3_batch():
    print("="*70)
    print("FAST BATCH UPLOAD TO PATIENT_DATA_V3")
    print("="*70)
    
    # Load 
    input_file = "synthea_structured.csv"
    records = []
    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        records = all_rows[:1500]

    print(f"Loaded {len(records)} records.")
    
    # Init
    print("\nInitializing...")
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    db = CyborgLiteManager()
    collection = "patient_data_v3"
    
    # Embeddings
    print("\nGenerating embeddings...")
    start_time = time.time()
    texts = [r.get('text_summary', '') for r in records]
    embeddings = embedder.encode(texts, show_progress_bar=True)
    embed_time = time.time()-start_time
    print(f"✓ Embeddings done in {embed_time:.1f}s")
    
    # Prepare Batch
    print("\nPreparing batch for CyborgDB...")
    items = []
    for i, (record, embedding) in enumerate(zip(records, embeddings)):
        meta = {k:v for k,v in record.items() if k != 'embedding'}
        pid = record.get('patient_id', 'unknown')
        rid = record.get('record_id', f'rec-{i}')
        
        # Format expected by CyborgDB SDK
        item = {
            "id": str(rid),
            "vector": embedding.tolist(),
            "metadata": {
                "patient_id": pid,
                **meta
            }
        }
        items.append(item)
    
    # Batch Upload
    print(f"\nUploading {len(items)} items in ONE batch...")
    start_time = time.time()
    
    # Get index (uses my caching fix)
    index = db.get_index(collection)
    
    # Upsert all at once
    try:
        index.upsert(items)
        elapsed = time.time() - start_time
        print("\n" + "="*70)
        print("✓ UPLOAD SUCCESS!")
        print(f"Uploaded: {len(items)} records")
        print(f"Time: {elapsed:.2f}s")
        print(f"Speed: {len(items)/elapsed:.1f} rec/s")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Upload Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    upload_v3_batch()
