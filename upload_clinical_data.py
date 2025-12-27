"""
MASTER UPLOAD SCRIPT
Uploads ALL clinical records to CyborgDB in manageable chunks.
Target Index: patient_data_FINAL
"""

import json
import sys
import time
import os
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()

def run_upload():
    print("="*70)
    print("🚀 MASTER CLINICAL DATA UPLOAD")
    print("="*70)
    
    # 1. Load Data
    input_file = "synthea_structured_FIXED.json"
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found. Please run 'parse_preprocessed_synthea.py' first.")
        return

    print(f"Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_records = json.load(f)
        
    total_records = len(all_records)
    print(f"✓ Loaded {total_records:,} records.")
    
    # 2. Initialize Services
    print("\nInitializing AI Models & Database...")
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    db = CyborgLiteManager()
    collection = "patient_data_FINAL"
    
    # Ensure index exists
    index = db.get_index(collection)
    
    # 3. Process in Chunks
    CHUNK_SIZE = 500
    total_chunks = (total_records + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    print(f"\nStarting Upload: {total_chunks} chunks of {CHUNK_SIZE} records each.")
    global_start = time.time()
    
    for chunk_idx in range(total_chunks):
        chunk_start = chunk_idx * CHUNK_SIZE
        chunk_end = min((chunk_idx + 1) * CHUNK_SIZE, total_records)
        chunk_records = all_records[chunk_start:chunk_end]
        
        try:
            # A. Generate Embeddings (Batch)
            texts = [r.get('text_for_embedding', str(r)) for r in chunk_records]
            embeddings = embedder.encode(texts, batch_size=32, show_progress_bar=False)
            
            # B. Prepare for DB
            items = []
            for i, (record, embedding) in enumerate(zip(chunk_records, embeddings)):
                # Clean metadata
                meta = {
                    "record_type": record.get('record_type'),
                    "display": record.get('display'),
                    "loinc_code": record.get('loinc_code'),
                    "value": record.get('value'),
                    "unit": record.get('unit'),
                    "effective_date": record.get('effective_date'),
                    "text_summary": record.get('text_summary', '')
                }
                
                # Create Item
                item = {
                    "id": str(record.get('record_id', f"chunk-{chunk_idx}-{i}")),
                    "vector": embedding.tolist(),
                    "metadata": {
                        "patient_id": record.get('patient_id', 'unknown'),
                        **meta
                    }
                }
                items.append(item)
            
            # C. Upsert to DB
            index.upsert(items)
            
            # Progress Log
            progress = (chunk_idx + 1) / total_chunks * 100
            print(f"✓ Chunk {chunk_idx+1}/{total_chunks} ({progress:.1f}%) - Uploaded {len(items)} items")
            
        except KeyboardInterrupt:
            print("\n⚠ Upload paused by user.")
            return
        except Exception as e:
            print(f"❌ Error on chunk {chunk_idx+1}: {e}")
            # Continue to next chunk or retry logic could go here

    duration = time.time() - global_start
    print("\n" + "="*70)
    print(f"✅ UPLOAD COMPLETE in {duration/60:.1f} minutes")
    print(f"Total Records: {total_records:,}")
    print("="*70)

if __name__ == "__main__":
    run_upload()
