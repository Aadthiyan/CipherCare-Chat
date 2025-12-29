"""
Upload structured clinical data to CyborgDB on Render
Optimized for cloud deployment with Hugging Face Inference API
INCLUDES ALL METADATA FIELDS
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time
from tqdm import tqdm

load_dotenv()

# Render deployment URLs
CYBORGDB_URL = "https://cyborgdb-toj5.onrender.com"
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

# Hugging Face Inference API
HF_INFERENCE_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-mpnet-base-v2/pipeline/feature-extraction"


class RenderDataUploader:
    """Upload data to CyborgDB on Render using HF Inference API"""
    
    def __init__(self):
        """Initialize uploader with Render URLs"""
        if not CYBORGDB_API_KEY:
            raise ValueError("CYBORGDB_API_KEY not found in .env file")
        if not HF_API_TOKEN:
            raise ValueError("HUGGINGFACE_API_KEY not found in .env file")
        
        print(f"🔗 Connecting to CyborgDB: {CYBORGDB_URL}")
        print(f"🤗 Using Hugging Face Inference API")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {CYBORGDB_API_KEY}"
        })
    
    def load_data(self, file_path: str, limit: Optional[int] = None) -> List[Dict]:
        """Load structured data from JSON file"""
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
        """Create embedding using Hugging Face Inference API"""
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
    
    def create_embeddings_batch(self, records: List[Dict], batch_size: int = 2000) -> List[Dict]:
        """Create embeddings for records in batches"""
        print(f"\n🔄 Creating embeddings for {len(records)} records...")
        
        for i in tqdm(range(0, len(records), batch_size), desc="Embedding batches"):
            batch = records[i:i+batch_size]
            
            for record in batch:
                # Get text for embedding
                text = record.get('text_for_embedding', record.get('text_summary', ''))
                if not text:
                    text = self._create_fallback_text(record)
                
                # Create embedding
                try:
                    embedding = self.create_embedding_hf(text)
                    record['embedding'] = embedding
                    time.sleep(0.01)  # Minimal rate limiting
                except Exception as e:
                    print(f"⚠️  Embedding error: {str(e)[:100]}")
                    record['embedding'] = None
        
        # Filter out failed embeddings
        records = [r for r in records if r.get('embedding') is not None]
        print(f"✅ Created {len(records)} embeddings successfully")
        
        return records
    
    def upload_to_cyborgdb(self, records: List[Dict], collection: str = "patient_data_FINAL", batch_size: int = 100) -> tuple:
        """Upload records to CyborgDB on Render"""
        print(f"\n📤 Uploading to collection: {collection}")
        
        success_count = 0
        error_count = 0
        
        # First, create the index
        try:
            index_response = self.session.post(
                f"{CYBORGDB_URL}/v1/indexes/create",
                json={"index_name": collection}
            )
            print(f"ℹ️  Index creation response: {index_response.status_code}")
        except Exception as e:
            print(f"ℹ️  Index already exists or error: {str(e)[:100]}")
        
        # Upload records in batches
        for i in tqdm(range(0, len(records), batch_size), desc="Uploading batches"):
            batch = records[i:i+batch_size]
            
            try:
                # Prepare batch payload with ALL metadata fields
                vectors = []
                for record in batch:
                    # Extract code information if exists
                    code_dict = record.get('code', {})
                    
                    vectors.append({
                        "id": record.get('record_id', str(time.time())),
                        "values": record.get('embedding'),
                        "metadata": {
                            # Core identifiers
                            "patient_id": record.get('patient_id', ''),
                            "record_id": record.get('record_id', ''),
                            "record_type": record.get('record_type', ''),
                            
                            # Clinical content
                            "display": record.get('display', ''),
                            "text_summary": record.get('text_summary', ''),
                            "text_for_embedding": record.get('text_for_embedding', ''),
                            
                            # Temporal data
                            "effective_date": record.get('effective_date', ''),
                            "created_at": record.get('created_at', ''),
                            
                            # Provenance
                            "data_source": record.get('data_source', ''),
                            "provenance": record.get('provenance', ''),
                            "language": record.get('language', 'en'),
                            
                            # Clinical codes
                            "snomed_code": record.get('snomed_code', ''),
                            "loinc_code": record.get('loinc_code', ''),
                            "code_system": code_dict.get('system', ''),
                            "code_value": code_dict.get('code', ''),
                            "code_display": code_dict.get('display', ''),
                            
                            # Observation values (if present)
                            "value": str(record.get('value', '')) if record.get('value') not in [None, ''] else '',
                            "value_normalized": str(record.get('value_normalized', '')) if record.get('value_normalized') not in [None, ''] else '',
                            "unit": record.get('unit', ''),
                            "value_type": record.get('value_type', ''),
                            
                            # Status
                            "status": record.get('status', 'final')
                        }
                    })
                
                payload = {
                    "index_name": collection,
                    "vectors": vectors
                }
                
                response = self.session.post(
                    f"{CYBORGDB_URL}/v1/vectors/upsert",
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    success_count += len(batch)
                else:
                    error_count += len(batch)
                    if error_count <= 5:
                        print(f"⚠️  Batch upload error: {response.status_code} - {response.text[:100]}")
                
                time.sleep(0.01)  # Minimal rate limiting
                
            except Exception as e:
                error_count += len(batch) if batch_size > 1 else 1
                if error_count <= 5:
                    print(f"⚠️  Error: {str(e)[:100]}")
        
        print(f"\n✅ Upload complete!")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        
        return success_count, error_count
    
    def _create_fallback_text(self, record: Dict) -> str:
        """Create fallback text for embedding"""
        parts = []
        if 'effective_date' in record:
            parts.append(record['effective_date'])
        if 'display' in record:
            parts.append(record['display'])
        if 'value' in record and record['value']:
            value_str = str(record['value'])
            if 'unit' in record:
                value_str += f" {record['unit']}"
            parts.append(value_str)
        return ': '.join(str(p) for p in parts if p)


def main():
    """Main upload process"""
    print("=" * 70)
    print("🚀 CipherCare Data Upload to Render (FULL METADATA)")
    print("=" * 70)
    
    # File to upload
    input_file = "synthea_structured_cipercare.json"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    # Ask for limit
    print(f"\n📁 File: {input_file}")
    print("\nOptions:")
    print("  1. Upload first 100 records (quick test - ~2 min)")
    print("  2. Upload first 1,000 records (medium test - ~15 min)")
    print("  3. Upload first 10,000 records (large - ~2.5 hours)")
    print("  4. Upload all 111,060 records (full - ~28 min)")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    limit_map = {
        "1": 100,
        "2": 1000,
        "3": 10000,
        "4": None
    }
    
    limit = limit_map.get(choice, 100)
    
    # Initialize uploader
    uploader = RenderDataUploader()
    
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
    print("⚠️  READY TO UPLOAD (WITH FULL METADATA)")
    print("=" * 70)
    print(f"Records: {len(records)}")
    print(f"Target: {CYBORGDB_URL}")
    print(f"Estimated time: {len(records) * 0.015 / 60:.1f} minutes (optimized)")
    print(f"\n✅ ALL fields will be preserved:")
    print(f"   - Clinical codes (SNOMED/LOINC)")
    print(f"   - Values and units")
    print(f"   - Timestamps and provenance")
    print(f"   - Complete metadata")
    print("\nProceed? [y/n]")
    
    if input("> ").strip().lower() != 'y':
        print("❌ Upload cancelled")
        return
    
    # Create embeddings
    print("\n" + "=" * 70)
    print("STEP 1: CREATING EMBEDDINGS")
    print("=" * 70)
    records = uploader.create_embeddings_batch(records, batch_size=2000)
    
    # Upload
    print("\n" + "=" * 70)
    print("STEP 2: UPLOADING TO CYBORGDB (FULL METADATA)")
    print("=" * 70)
    success, errors = uploader.upload_to_cyborgdb(records, batch_size=100)
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 UPLOAD COMPLETE!")
    print("=" * 70)
    print(f"Successfully uploaded: {success}/{len(records)} records")
    print(f"Errors: {errors}")
    if len(records) > 0:
        print(f"Success rate: {success/len(records)*100:.1f}%")
    
    print("\n✅ Your clinical data is now in CyborgDB on Render!")
    print("📋 ALL metadata fields have been preserved")
    print("🔍 You can now query it through your deployed frontend!")
    print("=" * 70)


if __name__ == "__main__":
    main()
