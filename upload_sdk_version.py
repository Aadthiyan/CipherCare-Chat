"""
Upload patient data to CyborgDB using Python SDK (not HTTP API)
This version works with the deployed CyborgDB service
"""

import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from tqdm import tqdm
import requests

load_dotenv()

# Configuration
CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL", "https://cyborgdb-toj5.onrender.com")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

# Hugging Face Inference API (NEW ROUTER URL)
HF_INFERENCE_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-mpnet-base-v2/pipeline/feature-extraction"


class SDKDataUploader:
    """Upload data using CyborgDB Python SDK"""
    
    def __init__(self):
        if not CYBORGDB_API_KEY:
            raise ValueError("CYBORGDB_API_KEY not found in .env")
        if not HF_API_TOKEN:
            raise ValueError("HUGGINGFACE_API_KEY not found in .env")
        
        print(f"🔗 Connecting to CyborgDB: {CYBORGDB_URL}")
        print(f"🤗 Using Hugging Face Inference API")
        
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
        
        print(f"📂 Loading {file_path}...")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if limit:
            data = data[:limit]
            print(f"✅ Loaded {len(data)} records (limited)")
        else:
            print(f"✅ Loaded {len(data)} total records")
        
        return data
    
    def create_embedding_hf(self, text: str) -> List[float]:
        """Create embedding using Hugging Face API"""
        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            HF_INFERENCE_URL,
            headers=headers,
            json={"inputs": text}
        )
        
        if response.status_code != 200:
            raise Exception(f"HF API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def create_embeddings_batch(self, records: List[Dict]) -> List[Dict]:
        """Create embeddings for all records"""
        print(f"\n🔄 Creating embeddings for {len(records)} records...")
        
        for record in tqdm(records, desc="Creating embeddings"):
            # Get text for embedding
            text = record.get('text_for_embedding') or record.get('text_summary', '')
            if not text:
                # Create fallback text
                parts = []
                if 'effective_date' in record:
                    parts.append(record['effective_date'])
                if 'display' in record:
                    parts.append(record['display'])
                text = ': '.join(str(p) for p in parts if p) or "Unknown record"
            
            # Create embedding
            try:
                embedding = self.create_embedding_hf(text)
                record['embedding'] = embedding
                time.sleep(0.02)  # Rate limiting
            except Exception as e:
                print(f"\n⚠️  Embedding error: {str(e)[:100]}")
                record['embedding'] = None
        
        # Filter out failed embeddings
        records = [r for r in records if r.get('embedding') is not None]
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
    
    def upload_records(self, records: List[Dict], batch_size: int = 50):
        """Upload records to CyborgDB using SDK"""
        print(f"\n📤 Uploading {len(records)} records...")
        
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
                time.sleep(0.05)  # Small delay between batches
                
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
    print("🚀 CipherCare Data Upload (SDK Version)")
    print("=" * 70)
    
    # File to upload
    input_file = "synthea_structured_cipercare.json"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    # Ask for limit
    print(f"\n📁 File: {input_file}")
    print("\nOptions:")
    print("  1. Upload first 100 records (quick test - ~5 min)")
    print("  2. Upload first 1,000 records (medium test - ~30 min)")
    print("  3. Upload first 10,000 records (large - ~2 hours)")
    print("  4. Upload all records (full - ~several hours)")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    limit_map = {
        "1": 100,
        "2": 1000,
        "3": 10000,
        "4": None
    }
    
    limit = limit_map.get(choice, 100)
    
    # Initialize uploader
    try:
        uploader = SDKDataUploader()
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
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
    
    # Confirm
    print("\n" + "=" * 70)
    print("⚠️  READY TO UPLOAD")
    print("=" * 70)
    print(f"Records: {len(records)}")
    print(f"Target: {CYBORGDB_URL}")
    print(f"Estimated time: {len(records) * 0.02 / 60:.1f} minutes")
    print("\nProceed? [y/n]")
    
    if input("> ").strip().lower() != 'y':
        print("❌ Upload cancelled")
        return
    
    # Create embeddings
    print("\n" + "=" * 70)
    print("STEP 1: CREATING EMBEDDINGS")
    print("=" * 70)
    records = uploader.create_embeddings_batch(records)
    
    # Setup index
    print("\n" + "=" * 70)
    print("STEP 2: SETTING UP INDEX")
    print("=" * 70)
    uploader.get_or_create_index("patient_records_v1")
    
    # Upload
    print("\n" + "=" * 70)
    print("STEP 3: UPLOADING TO CYBORGDB")
    print("=" * 70)
    success, errors = uploader.upload_records(records, batch_size=50)
    
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
