"""
FIXED Upload Script - Properly handles index creation and batch uploads
This version creates the index ONCE and uses true batch operations
"""

import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import cyborgdb
from cyborgdb.openapi_client.models import IndexKey, IndexOperationRequest
import time

load_dotenv()


class FixedUploader:
    """Fixed uploader that handles index creation properly"""
    
    def __init__(self):
        self.embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        self.client = cyborgdb.Client(
            api_key=os.getenv("CYBORGDB_API_KEY"),
            base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
        )
        self.index = None
        print("Initialized uploader")
    
    def get_or_create_index(self, index_name: str = "patient_data_v2"):
        """Create index ONCE and cache it"""
        if self.index is not None:
            return self.index
        
        print(f"\nGetting/creating index: {index_name}")
        
        # Generate deterministic key
        api_key = os.getenv("CYBORGDB_API_KEY", "default")
        combined = f"{api_key}:{index_name}"
        index_key_bytes = hashlib.sha256(combined.encode()).digest()
        
        # Try to load existing index first
        try:
            print("  Attempting to load existing index...")
            self.index = self.client.load_index(
                index_name=index_name,
                index_key=index_key_bytes
            )
            print(f"  ✓ Loaded existing index: {index_name}")
            return self.index
        except Exception as load_error:
            print(f"  Index doesn't exist, creating new one...")
        
        # Create new index
        try:
            self.index = self.client.create_index(
                index_name=index_name,
                index_key=index_key_bytes
            )
            print(f"  ✓ Created new index: {index_name}")
            return self.index
        except Exception as create_error:
            error_msg = str(create_error).lower()
            if "already exists" in error_msg:
                # If creation failed because it exists, load it
                print("  Index was created by another process, loading it...")
                self.index = self.client.load_index(
                    index_name=index_name,
                    index_key=index_key_bytes
                )
                print(f"  ✓ Loaded index: {index_name}")
                return self.index
            else:
                raise Exception(f"Failed to create/load index: {create_error}")
    
    def upload_batch(self, records: List[Dict], collection: str = "patient_data_v2"):
        """Upload records in batches with proper index handling"""
        
        print(f"\n{'='*70}")
        print("UPLOADING TO CYBORGDB")
        print(f"{'='*70}")
        print(f"Records: {len(records)}")
        print(f"Collection: {collection}")
        
        # Get/create index ONCE
        index = self.get_or_create_index(collection)
        
        # Create embeddings
        print(f"\nCreating embeddings...")
        start_time = time.time()
        
        texts = [r.get('text_for_embedding', r.get('text_summary', '')) for r in records]
        embeddings = self.embedder.encode(texts, show_progress_bar=True)
        
        embed_time = time.time() - start_time
        print(f"✓ Embeddings created in {embed_time:.1f}s ({len(records)/embed_time:.1f} rec/sec)")
        
        # Upload in batches
        print(f"\nUploading records...")
        start_time = time.time()
        batch_size = 100
        success_count = 0
        error_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            
            for record, embedding in zip(batch, batch_embeddings):
                try:
                    # Prepare data
                    record_id = record.get('record_id', f"rec-{i}")
                    patient_id = record.get('patient_id', 'unknown')
                    metadata = {k: v for k, v in record.items() if k not in ['embedding']}
                    
                    # Upsert using the CACHED index
                    index.upsert(
                        id=record_id,
                        vector=embedding.tolist(),
                        metadata=metadata
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        print(f"  Error on record {i}: {str(e)[:100]}")
            
            # Progress update
            processed = min(i + batch_size, len(records))
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (len(records) - processed) / rate if rate > 0 else 0
            
            if processed % 100 == 0 or processed == len(records):
                print(f"  {processed}/{len(records)} ({processed/len(records)*100:.1f}%) - "
                      f"Success: {success_count}, Errors: {error_count} - "
                      f"Rate: {rate:.1f} rec/sec - ETA: {eta:.0f}s")
        
        total_time = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"✓ Upload complete!")
        print(f"  Time: {total_time:.1f}s")
        print(f"  Success: {success_count}/{len(records)} ({success_count/len(records)*100:.1f}%)")
        print(f"  Errors: {error_count}")
        print(f"  Rate: {success_count/total_time:.1f} rec/sec")
        print(f"{'='*70}")


def main():
    print(f"{'='*70}")
    print("FIXED STRUCTURED DATA UPLOADER")
    print(f"{'='*70}")
    
    # Load data
    input_file = "synthea_structured_FIXED.json"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"\nLoading {input_file}...")
    with open(input_file, 'r') as f:
        all_records = json.load(f)
    
    print(f"Total records in file: {len(all_records)}")
    
    # Ask for limit
    print(f"\nOptions:")
    print(f"  1. Upload first 1,000 records (~5 min)")
    print(f"  2. Upload first 10,000 records (~30 min)")
    print(f"  3. Upload all {len(all_records)} records (~{len(all_records)/200:.0f} min)")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    if choice == "1":
        records = all_records[:1000]
    elif choice == "2":
        records = all_records[:10000]
    else:
        records = all_records
    
    print(f"\n✓ Selected {len(records)} records")
    
    # Show stats
    by_type = {}
    for r in records:
        rtype = r.get('record_type', 'unknown')
        by_type[rtype] = by_type.get(rtype, 0) + 1
    
    print(f"\nBy type:")
    for rtype, count in sorted(by_type.items()):
        print(f"  {rtype}: {count}")
    
    # Confirm
    print(f"\n{'='*70}")
    print("READY TO UPLOAD")
    print(f"{'='*70}")
    confirm = input("Proceed? [y/n]: ").strip().lower()
    
    if confirm != 'y':
        print("❌ Upload cancelled")
        return
    
    # Upload
    uploader = FixedUploader()
    uploader.upload_batch(records, collection="patient_data_v2")
    
    print("\n✓ Done! You can now test your chatbot.")


if __name__ == "__main__":
    main()
