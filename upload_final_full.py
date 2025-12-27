"""
INCREMENTAL UPLOAD TO PATIENT_DATA_FINAL
Uploads data in chunks with FILE LOGGING for observability.
"""

import json
import sys
import time
import logging
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()

# Setup logging to file
logging.basicConfig(
    filename='upload_progress.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    filemode='w' # Overwrite previous log
)

def chunked_upload():
    print("Starting upload... check upload_progress.log")
    logging.info("STARTING UPLOAD OF ALL RECORDS")
    
    # Load JSON
    input_file = "synthea_structured_FIXED.json"
    logging.info(f"Loading {input_file}...")
    try:
        with open(input_file, 'r') as f:
            all_records = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found!")
        return
        
    records_to_upload = all_records
    total_count = len(records_to_upload)
    logging.info(f"Total to upload: {total_count}")
    print(f"Loaded {total_count} records. Processing...")

    # Init
    logging.info("Initializing services...")
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    db = CyborgLiteManager()
    collection = "patient_data_FINAL"
    index = db.get_index(collection)
    
    # Chunk size
    CHUNK_SIZE = 1000  
    total_chunks = (total_count + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    start_time = time.time()
    
    for chunk_idx in range(total_chunks):
        chunk_start = chunk_idx * CHUNK_SIZE
        chunk_end = min((chunk_idx + 1) * CHUNK_SIZE, total_count)
        chunk_records = records_to_upload[chunk_start:chunk_end]
        
        # 1. Embed (Batch 64 for speed on CPU)
        try:
            texts = [r.get('text_for_embedding', str(r)) for r in chunk_records]
            embeddings = embedder.encode(texts, batch_size=64, show_progress_bar=False)
            
            # 2. Prepare Items
            items = []
            for i, (record, embedding) in enumerate(zip(chunk_records, embeddings)):
                meta = {
                    "record_type": record.get('record_type'),
                    "display": record.get('display'),
                    "loinc_code": record.get('loinc_code'),
                    "value": record.get('value'),
                    "unit": record.get('unit'),
                    "effective_date": record.get('effective_date'),
                    "text_summary": record.get('text_summary', '')
                }
                
                item = {
                    "id": str(record.get('record_id')),
                    "vector": embedding.tolist(),
                    "metadata": {
                        "patient_id": record.get('patient_id', 'unknown'),
                        **meta
                    }
                }
                items.append(item)
                
            # 3. Upsert Chunk
            index.upsert(items)
            elapsed = time.time() - start_time
            avg_speed = chunk_end / elapsed
            logging.info(f"✓ Chunk {chunk_idx+1}/{total_chunks} ({len(items)} items). Total: {chunk_end}/{total_count}. Speed: {avg_speed:.1f} rec/s")
            
            # Print to console occasionally too
            if (chunk_idx+1) % 5 == 0:
                print(f"Uploaded {chunk_end}/{total_count} records ({int(chunk_end/total_count*100)}%)")
                
        except Exception as e:
            logging.error(f"❌ Error on chunk {chunk_idx+1}: {e}")
            print(f"Error on chunk {chunk_idx+1}: {e}")

    logging.info("UPLOAD COMPLETE")
    print("\n" + "="*70)
    print("✓ UPLOAD COMPLETE")
    print("="*70)

if __name__ == "__main__":
    chunked_upload()
