"""
Fast upload using LOCAL embedding model (no API calls)
This is 50-100x faster than API-based embedding
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configuration
CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL", "https://cyborgdb-toj5.onrender.com")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")


class FastSDKUploader:
    """Upload data using LOCAL embeddings (much faster)"""
    
    def __init__(self):
        if not CYBORGDB_API_KEY:
            raise ValueError("CYBORGDB_API_KEY not found in .env")
        
        print(f"🔗 Connecting to CyborgDB: {CYBORGDB_URL}")
        print(f"🚀 Using LOCAL embedding model (FAST)")
        
        # Initialize local embedder
        print("\n📥 Loading embedding model locally...")
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        print("✅ Model loaded!")
        
        # Initialize CyborgDB client
        import cyborgdb
        self.client = cyborgdb.Client(
            api_key=CYBORGDB_API_KEY,
            base_url=CYBORGDB_URL
        )
        self.index = None
    
    def load_data(self, file_path: str, limit: int = None) -> List[Dict]:
        """Load patient data from JSON"""
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return []
        
        print(f"\n📂 Loading {file_path}...")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if limit:
            data = data[:limit]
            print(f"✅ Loaded {len(data)} records (limited)")
        else:
            print(f"✅ Loaded {len(data)} total records")
        
        return data
    
    def create_embeddings_batch(self, records: List[Dict], batch_size: int = 256) -> List[Dict]:
        """Create embeddings in BATCHES using local model (FAST!)"""
        print(f"\n🔄 Creating embeddings for {len(records)} records...")
        print(f"   Batch size: {batch_size} (processing {batch_size} at once)")
        
        # Prepare all texts first
        texts = []
        for record in records:
            text = record.get('text_for_embedding') or record.get('text_summary', '')
            if not text:
                # Create fallback text
                parts = []
                if 'effective_date' in record:
                    parts.append(record['effective_date'])
                if 'display' in record:
                    parts.append(record['display'])
                text = ': '.join(str(p) for p in parts if p) or "Unknown record"
            texts.append(text)
        
        # Generate embeddings in batches (MUCH FASTER!)
        all_embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Creating embeddings"):
            batch_texts = texts[i:i+batch_size]
            # This processes entire batch at once!
            batch_embeddings = self.embedder.encode(batch_texts, show_progress_bar=False)
            all_embeddings.extend(batch_embeddings.tolist())
        
        # Assign embeddings to records
        for i, record in enumerate(records):
            record['embedding'] = all_embeddings[i]
        
        print(f"✅ Created {len(records)} embeddings successfully")
        return records
    
    def get_or_create_index(self, index_name: str):
        """Get or create CyborgDB index using SDK"""
        print(f"\n📊 Setting up index: {index_name}")
        
        # Create deterministic key
        combined = f"{CYBORGDB_API_KEY}:{index_name}"
        index_key = hashlib.sha256(combined.encode()).digest()
        
        try:
            # Try to create
            self.index = self.client.create_index(
                index_name=index_name,
                index_key=index_key
            )
            print(f"✅ Created new index '{index_name}'")
        except Exception as e:
            if "already exists" in str(e).lower():
                # Load existing
                print(f"ℹ️  Index already exists, loading...")
                self.index = self.client.load_index(
                    index_name=index_name,
                    index_key=index_key
                )
                print(f"✅ Loaded existing index '{index_name}'")
            else:
                raise
    
    def upload_records(self, records: List[Dict], batch_size: int = 100):
        """Upload records to CyborgDB using SDK"""
        print(f"\n📤 Uploading {len(records)} records...")
        print(f"   Upload batch size: {batch_size}")
        
        success_count = 0
        error_count = 0
        
        for i in tqdm(range(0, len(records), batch_size), desc="Uploading batches"):
            batch = records[i:i+batch_size]
            
            try:
                # Prepare items for SDK
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
                
                # Upload using SDK
                self.index.upsert(items)
                success_count += len(batch)
                time.sleep(0.02)  # Small delay between batches
                
            except Exception as e:
                error_count += len(batch)
                if error_count <= 5:
                    print(f"\n⚠️  Batch error: {str(e)[:100]}")
        
        print(f"\n✅ Upload complete!")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        
        return success_count, error_count


def main():
    """Main upload process"""
    print("=" * 70)
    print("🚀 CipherCare FAST Data Upload (Local Embeddings)")
    print("=" * 70)
    
    # File to upload
    input_file = "synthea_structured_cipercare.json"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    # Ask for limit
    print(f"\n📁 File: {input_file}")
    print("\nOptions:")
    print("  1. Upload first 1,000 records (test - ~2 min)")
    print("  2. Upload first 10,000 records (medium - ~10 min)")
    print("  3. Upload first 50,000 records (large - ~30 min)")
    print("  4. Upload all 111,060 records (full - ~60 min)")
    print("  5. Upload 76,317 records (150 patients - RECOMMENDED for free tier - ~8 min)")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    limit_map = {
        "1": 1000,
        "2": 10000,
        "3": 50000,
        "4": None,
        "5": 76317
    }
    
    limit = limit_map.get(choice, 1000)
    
    # Initialize uploader
    try:
        uploader = FastSDKUploader()
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        print("\nMake sure sentence-transformers is installed:")
        print("   pip install sentence-transformers")
        return
    
    # Load data
    records = uploader.load_data(input_file, limit=limit)
    if not records:
        print("❌ No records loaded")
        return
    
    # Show statistics
    patients = set(r.get('patient_id') for r in records)
    record_types = {}
    for record in records:
        rtype = record.get('record_type', 'unknown')
        record_types[rtype] = record_types.get(rtype, 0) + 1
    
    print("\n" + "=" * 70)
    print("📊 DATASET STATISTICS")
    print("=" * 70)
    print(f"Total records: {len(records)}")
    print(f"Unique patients: {len(patients)}")
    print(f"\nBy type:")
    for rtype, count in sorted(record_types.items()):
        print(f"  {rtype}: {count}")
    
    # Estimate time
    embedding_time = len(records) * 0.003  # ~3ms per record in batches
    upload_time = len(records) * 0.02 / 100  # 20ms per batch of 100
    total_time = (embedding_time + upload_time) / 60
    
    # Confirm
    print("\n" + "=" * 70)
    print("⚠️  READY TO UPLOAD")
    print("=" * 70)
    print(f"Records: {len(records)}")
    print(f"Target: {CYBORGDB_URL}")
    print(f"Estimated time: {total_time:.1f} minutes (LOCAL embeddings)")
    print("\nProceed? [y/n]")
    
    if input("> ").strip().lower() != 'y':
        print("❌ Upload cancelled")
        return
    
    # Create embeddings (FAST!)
    print("\n" + "=" * 70)
    print("STEP 1: CREATING EMBEDDINGS (LOCAL - FAST!)")
    print("=" * 70)
    records = uploader.create_embeddings_batch(records, batch_size=256)
    
    # Setup index
    print("\n" + "=" * 70)
    print("STEP 2: SETTING UP INDEX")
    print("=" * 70)
    uploader.get_or_create_index("patient_records_v1")
    
    # Upload
    print("\n" + "=" * 70)
    print("STEP 3: UPLOADING TO CYBORGDB")
    print("=" * 70)
    success, errors = uploader.upload_records(records, batch_size=100)
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 UPLOAD COMPLETE!")
    print("=" * 70)
    print(f"Successfully uploaded: {success}/{len(records)} records")
    print(f"Errors: {errors}")
    if len(records) > 0:
        print(f"Success rate: {success/len(records)*100:.1f}%")
    
    print("\n✅ Your clinical data is now in CyborgDB!")
    print("🔍 You can now query it through your backend!")
    print("=" * 70)


if __name__ == "__main__":
    main()
