"""
Upload structured clinical data to CyborgDB on Render
Uses the SAME method as your backend - CyborgLiteManager with Python SDK
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time
from tqdm import tqdm
import uuid

# Import the same manager your backend uses
from backend.cyborg_lite_manager import CyborgLiteManager
from embeddings.embedder import ClinicalEmbedder

load_dotenv()

# Configure for Render deployment
os.environ["CYBORGDB_BASE_URL"] = "https://cyborgdb-toj5.onrender.com"


class RenderDataUploaderSDK:
    """Upload data using the same SDK as your backend"""
    
    def __init__(self):
        """Initialize using backend's approach"""
        print("🔗 Connecting to CyborgDB on Render...")
        print(f"   URL: {os.getenv('CYBORGDB_BASE_URL')}")
        
        # Use the same embedder as your backend
        self.embedder = ClinicalEmbedder()
        print("✅ Embedder initialized (HuggingFace Inference API)")
        
        # Use the same CyborgDB manager as your backend
        self.db = CyborgLiteManager()
        print("✅ CyborgDB manager initialized")
    
    def load_data(self, file_path: str, limit: Optional[int] = None) -> List[Dict]:
        """Load structured data from JSON file"""
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
    
    def create_embeddings_batch(self, records: List[Dict], batch_size: int = 100) -> List[Dict]:
        """Create embeddings using backend's embedder"""
        print(f"\n🔄 Creating embeddings for {len(records)} records...")
        print("   (Using HuggingFace Inference API - same as backend)")
        
        for i in tqdm(range(0, len(records), batch_size), desc="Embedding batches"):
            batch = records[i:i+batch_size]
            
            for record in batch:
                # Get text for embedding
                text = record.get('text_for_embedding', record.get('text_summary', ''))
                if not text:
                    text = self._create_fallback_text(record)
                
                # Create embedding using backend's method
                try:
                    embedding = self.embedder.get_embedding(text)
                    record['embedding'] = embedding
                except Exception as e:
                    print(f"\n⚠️  Embedding error: {str(e)[:100]}")
                    record['embedding'] = None
        
        # Filter out failed embeddings
        records = [r for r in records if r.get('embedding') is not None]
        print(f"✅ Created {len(records)} embeddings successfully")
        
        return records
    
    def upload_to_cyborgdb(self, records: List[Dict], collection: str = "patient_records_v1") -> tuple:
        """Upload using backend's upsert method"""
        print(f"\n📤 Uploading to collection: {collection}")
        print("   (Using same method as backend)")
        
        success_count = 0
        error_count = 0
        
        # Upload records one by one using backend's method
        for record in tqdm(records, desc="Uploading records"):
            try:
                # Prepare metadata with ALL fields
                code_dict = record.get('code', {})
                
                metadata = {
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
                    
                    # Observation values
                    "value": str(record.get('value', '')) if record.get('value') not in [None, ''] else '',
                    "value_normalized": str(record.get('value_normalized', '')) if record.get('value_normalized') not in [None, ''] else '',
                    "unit": record.get('unit', ''),
                    "value_type": record.get('value_type', ''),
                    
                    # Status
                    "status": record.get('status', 'final')
                }
                
                # Use backend's upsert method (same as main.py uses)
                self.db.upsert(
                    record_id=record.get('record_id', str(uuid.uuid4())),
                    patient_id=record.get('patient_id', 'unknown'),
                    embedding=record['embedding'],
                    metadata=metadata,
                    collection=collection
                )
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"\n⚠️  Upload error: {str(e)[:100]}")
        
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
    print("🚀 CipherCare Data Upload (Using Backend Method)")
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
    print("  2. Upload first 1,000 records (medium test - ~20 min)")
    print("  3. Upload first 10,000 records (large - ~3 hours)")
    print("  4. Upload all 111,060 records (full - ~5-6 hours)")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    limit_map = {
        "1": 100,
        "2": 1000,
        "3": 10000,
        "4": None
    }
    
    limit = limit_map.get(choice, 100)
    
    # Initialize uploader
    uploader = RenderDataUploaderSDK()
    
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
    print(f"Target: https://cyborgdb-toj5.onrender.com")
    print(f"Method: Same as backend (CyborgLiteManager)")
    print(f"\n✅ ALL metadata fields will be preserved")
    print("\nProceed? [y/n]")
    
    if input("> ").strip().lower() != 'y':
        print("❌ Upload cancelled")
        return
    
    # Create embeddings
    print("\n" + "=" * 70)
    print("STEP 1: CREATING EMBEDDINGS")
    print("=" * 70)
    records = uploader.create_embeddings_batch(records, batch_size=100)
    
    # Upload
    print("\n" + "=" * 70)
    print("STEP 2: UPLOADING TO CYBORGDB")
    print("=" * 70)
    success, errors = uploader.upload_to_cyborgdb(records)
    
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
