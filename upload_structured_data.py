"""
Fixed upload script for structured clinical data to CipherCare/CyborgDB
Handles existing indexes and provides progress monitoring
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv
import uuid
import time
from datetime import datetime

load_dotenv()


class StructuredDataUploaderFixed:
    """Upload structured clinical observations to CyborgDB with progress tracking"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """Initialize uploader"""
        print(" Initializing uploader...")
        self.embedder = SentenceTransformer(model_name)
        self.db = CyborgLiteManager()
        print(f" Initialized with model: {model_name}")
    
    def load_data(self, file_path: str, limit: Optional[int] = None) -> List[Dict]:
        """Load structured data from JSON file"""
        path = Path(file_path)
        
        if not path.exists():
            print(f" File not found: {file_path}")
            return []
        
        print(f" Loading {file_path}...")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if limit:
            data = data[:limit]
            print(f" Loaded {len(data)} records (limited from total)")
        else:
            print(f" Loaded {len(data)} records")
        
        return data
    
    def create_embeddings_batch(self, records: List[Dict], batch_size: int = 2000) -> List[Dict]:
        """Create embeddings in batches with progress tracking"""
        print(f" Creating embeddings in batches of {batch_size}...")
        
        total = len(records)
        start_time = time.time()
        
        for i in range(0, total, batch_size):
            batch = records[i:i+batch_size]
            
            # Extract texts for batch
            texts = []
            for record in batch:
                text = record.get('text_for_embedding', record.get('text_summary', ''))
                if not text:
                    text = self._create_fallback_text(record)
                texts.append(text)
            
            # Create embeddings for batch
            embeddings = self.embedder.encode(texts, show_progress_bar=False)
            
            # Assign embeddings back to records
            for record, embedding in zip(batch, embeddings):
                record['embedding'] = embedding.tolist()
            
            # Progress update
            processed = min(i + batch_size, total)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed) / rate if rate > 0 else 0
            
            print(f"   {processed}/{total} embeddings created ({processed/total*100:.1f}%) - "
                  f"Rate: {rate:.1f} rec/sec - ETA: {eta/60:.1f} min")
        
        print(f" All embeddings created in {(time.time()-start_time)/60:.1f} minutes")
        return records
    
    def upload_to_cyborgdb_batch(
        self,
        records: List[Dict],
        collection: str = "patient_data_v2",
        batch_size: int = 1000
    ):
        """Upload records to CyborgDB in batches with error handling"""
        print(f" Uploading to collection: {collection}")
        
        total = len(records)
        success_count = 0
        error_count = 0
        start_time = time.time()
        
        # Group by patient for better organization
        by_patient = {}
        for record in records:
            patient_id = record.get('patient_id', 'unknown')
            if patient_id not in by_patient:
                by_patient[patient_id] = []
            by_patient[patient_id].append(record)
        
        print(f"  Uploading data for {len(by_patient)} patients...")
        
        all_records = []
        for patient_records in by_patient.values():
            all_records.extend(patient_records)
        
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i+batch_size]
            
            for record in batch:
                try:
                    # Prepare metadata
                    metadata = self._prepare_metadata(record)
                    
                    # Upload to CyborgDB (skip index creation, use existing)
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
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"    Error: {str(e)[:100]}")
            
            # Progress update
            processed = min(i + batch_size, len(all_records))
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (len(all_records) - processed) / rate if rate > 0 else 0
            
            if processed % 1000 == 0 or processed == len(all_records):
                print(f"   {processed}/{len(all_records)} uploaded ({processed/len(all_records)*100:.1f}%) - "
                      f"Success: {success_count}, Errors: {error_count} - "
                      f"Rate: {rate:.1f} rec/sec - ETA: {eta/60:.1f} min")
        
        elapsed_total = time.time() - start_time
        print(f"\n Upload complete in {elapsed_total/60:.1f} minutes!")
        print(f"  Success: {success_count}")
        print(f"  Errors: {error_count}")
        
        return success_count, error_count
    
    def _prepare_metadata(self, record: Dict) -> Dict:
        """Prepare metadata for CyborgDB storage"""
        metadata = {k: v for k, v in record.items() if k != 'embedding'}
        metadata.setdefault('record_type', 'observation')
        metadata.setdefault('data_source', 'unknown')
        metadata.setdefault('status', 'final')
        
        if 'code' in metadata and isinstance(metadata['code'], dict):
            metadata['code_system'] = metadata['code'].get('system', '')
            metadata['code_value'] = metadata['code'].get('code', '')
            metadata['code_display'] = metadata['code'].get('display', '')
        
        return metadata
    
    def _create_fallback_text(self, record: Dict) -> str:
        """Create fallback text for embedding"""
        parts = []
        if 'effective_date' in record:
            parts.append(record['effective_date'])
        if 'display' in record:
            parts.append(record['display'])
        if 'value' in record and record['value'] is not None:
            value_str = f"{record['value']}"
            if 'unit' in record:
                value_str += f" {record['unit']}"
            parts.append(value_str)
        return ': '.join(str(p) for p in parts if p)


def main():
    """Main execution with progress monitoring"""
    print("="*70)
    print(" Structured Clinical Data Uploader for CipherCare (Fixed)")
    print("="*70)
    
    # Get input file
    input_file = "synthea_structured_FIXED.json"
    
    if not Path(input_file).exists():
        print(f" File not found: {input_file}")
        return
    
    # Ask for limit
    print(f"\n File: {input_file}")
    print(" This file has 111,060 records. You can upload all or a subset for testing.")
    print("\nOptions:")
    print("  1. Upload first 1,000 records (quick test - ~5 min)")
    print("  2. Upload first 10,000 records (medium test - ~30 min)")
    print("  3. Upload all 111,060 records (full upload - ~3 hours)")
    
    choice = input("\nSelect option [1]: ").strip() or "1"
    
    limit_map = {
        "1": 1000,
        "2": 10000,
        "3": None
    }
    
    limit = limit_map.get(choice, 1000)
    
    # Initialize uploader
    uploader = StructuredDataUploaderFixed()
    
    # Load data
    records = uploader.load_data(input_file, limit=limit)
    
    if not records:
        print(" No records loaded")
        return
    
    # Show statistics
    record_types = {}
    for record in records:
        rtype = record.get('record_type', 'unknown')
        record_types[rtype] = record_types.get(rtype, 0) + 1
    
    print("\n" + "="*70)
    print(" DATASET STATISTICS")
    print("="*70)
    print(f"Total records to upload: {len(records)}")
    print(f"\nBy type:")
    for rtype, count in sorted(record_types.items()):
        print(f"   {rtype}: {count}")
    
    # Confirm
    print("\n" + "="*70)
    print("  READY TO UPLOAD")
    print("="*70)
    print(f"Records: {len(records)}")
    print(f"Collection: patient_embeddings")
    print(f"Estimated time: {len(records)/400:.1f} minutes (optimized batching)")
    print("\nProceed? [y/n]")
    
    if input("> ").strip().lower() != 'y':
        print(" Upload cancelled")
        return
    
    # Create embeddings
    print("\n" + "="*70)
    print("STEP 1: CREATING EMBEDDINGS")
    print("="*70)
    records = uploader.create_embeddings_batch(records, batch_size=2000)
    
    # Upload
    print("\n" + "="*70)
    print("STEP 2: UPLOADING TO CYBORGDB")
    print("="*70)
    success, errors = uploader.upload_to_cyborgdb_batch(records, batch_size=1000)
    
    # Summary
    print("\n" + "="*70)
    print(" UPLOAD COMPLETE!")
    print("="*70)
    print(f"Successfully uploaded: {success}/{len(records)} records")
    print(f"Errors: {errors}")
    print(f"Success rate: {success/len(records)*100:.1f}%")
    
    print("\n Your structured clinical data is now in CyborgDB!")
    print("You can now query it through the CipherCare chatbot.")
    print("="*70)


if __name__ == "__main__":
    main()
