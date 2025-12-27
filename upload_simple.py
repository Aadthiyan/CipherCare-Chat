"""
SIMPLEST WORKING UPLOAD - Uses existing batch_upsert from cyborg_lite_manager
"""

import json
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()
from backend.cyborg_lite_manager import CyborgLiteManager
import time


def main():
    print("="*70)
    print("SIMPLE BATCH UPLOADER")
    print("="*70)
    
    # Load data
    input_file = "synthea_structured_FIXED.json"
    
    print(f"\nLoading {input_file}...")
    with open(input_file, 'r') as f:
        all_records = json.load(f)
    
    print(f"Total records: {len(all_records)}")
    
    # Get first 1000
    records = all_records[:1000]
    print(f"Uploading: {len(records)} records")
    
    # Show stats
    by_type = {}
    for r in records:
        rtype = r.get('record_type', 'unknown')
        by_type[rtype] = by_type.get(rtype, 0) + 1
    
    print(f"\nBy type:")
    for rtype, count in sorted(by_type.items()):
        print(f"  {rtype}: {count}")
    
    # Confirm
    confirm = input("\nProceed? [y/n]: ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return
    
    # Initialize
    print("\nInitializing...")
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    db = CyborgLiteManager()
    
    # Create embeddings
    print("\nCreating embeddings...")
    start = time.time()
    
    texts = [r.get('text_for_embedding', r.get('text_summary', '')) for r in records]
    embeddings = embedder.encode(texts, show_progress_bar=True)
    
    print(f"✓ Embeddings done in {time.time()-start:.1f}s")
    
    # Prepare records with embeddings
    print("\nPreparing records...")
    upload_records = []
    for record, embedding in zip(records, embeddings):
        upload_records.append({
            'id': record.get('record_id', ''),
            'patient_id': record.get('patient_id', ''),
            'embedding': embedding.tolist(),
            'metadata': {k: v for k, v in record.items() if k not in ['embedding']}
        })
    
    # Upload using batch_upsert
    print(f"\nUploading {len(upload_records)} records...")
    start = time.time()
    
    try:
        count = db.batch_upsert(upload_records, collection="patient_data_v2")
        elapsed = time.time() - start
        print(f"\n✓ SUCCESS!")
        print(f"  Uploaded: {count} records")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Rate: {count/elapsed:.1f} rec/sec")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
