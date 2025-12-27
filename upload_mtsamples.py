"""
Upload MTSamples clinical notes to CipherCare/CyborgDB
Optimized for rich clinical narratives and semantic search
"""

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()


def load_mtsamples_data(file_path: str = "mtsamples_cipercare.json") -> List[Dict]:
    """Load MTSamples data"""
    
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        print("💡 Run 'python download_mtsamples.py' first")
        return []
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data)} clinical records")
    return data


def create_embeddings(patients: List[Dict], model_name: str = "sentence-transformers/all-mpnet-base-v2"):
    """Create embeddings for clinical notes"""
    
    print(f"🔄 Loading embedding model: {model_name}")
    embedder = SentenceTransformer(model_name)
    
    print("🔄 Creating embeddings...")
    
    for idx, patient in enumerate(patients):
        # Use the full clinical text for embeddings
        text = patient.get('full_text', patient.get('clinical_note', ''))
        
        # Create embedding
        embedding = embedder.encode(text).tolist()
        patient['embedding'] = embedding
        
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(patients)} records...")
    
    print(f"✓ Created embeddings for {len(patients)} records")
    return patients


def upload_to_cyborgdb(patients: List[Dict], collection: str = "patient_embeddings"):
    """Upload to CyborgDB"""
    
    print(f"🔄 Connecting to CyborgDB...")
    
    try:
        db = CyborgLiteManager()
        print("✓ Connected to CyborgDB")
    except Exception as e:
        print(f"❌ Failed to connect to CyborgDB: {e}")
        return
    
    print(f"🔄 Uploading to collection: {collection}")
    
    success_count = 0
    error_count = 0
    
    for idx, patient in enumerate(patients):
        try:
            # Prepare metadata (everything except embedding)
            metadata = {
                "patient_id": patient['patient_id'],
                "specialty": patient.get('specialty', 'General'),
                "description": patient.get('description', ''),
                "sample_name": patient.get('sample_name', ''),
                "keywords": patient.get('keywords', ''),
                "source": patient.get('source', 'MTSamples'),
                "category": patient.get('category', 'clinical_note'),
                "text": patient.get('clinical_note', '')[:500]  # First 500 chars for preview
            }
            
            # Upload to CyborgDB
            db.upsert(
                record_id=str(uuid.uuid4()),
                patient_id=patient['patient_id'],
                embedding=patient['embedding'],
                metadata=metadata,
                collection=collection
            )
            
            success_count += 1
            
            if (idx + 1) % 100 == 0:
                print(f"  Uploaded {idx + 1}/{len(patients)} records...")
        
        except Exception as e:
            error_count += 1
            print(f"  ⚠️  Error uploading {patient['patient_id']}: {e}")
    
    print(f"\n✓ Upload complete!")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")


def test_query(db: CyborgLiteManager, query: str = "cardiovascular disease"):
    """Test a sample query"""
    
    print(f"\n🔍 Testing query: '{query}'")
    
    try:
        # Create query embedding
        embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        query_embedding = embedder.encode(query).tolist()
        
        # Search
        results = db.search(
            query_embedding=query_embedding,
            collection="patient_embeddings",
            top_k=5
        )
        
        print(f"✓ Found {len(results)} results:")
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            print(f"\n  {i}. Patient: {metadata.get('patient_id')}")
            print(f"     Specialty: {metadata.get('specialty')}")
            print(f"     Description: {metadata.get('description', '')[:100]}...")
            print(f"     Score: {result.get('score', 0):.4f}")
    
    except Exception as e:
        print(f"❌ Query failed: {e}")


def main():
    """Main execution"""
    
    print("🏥 MTSamples Upload to CipherCare")
    print("="*60)
    
    # Check if user wants to use sample data first
    sample_file = Path("mtsamples_sample_10.json")
    full_file = Path("mtsamples_cipercare.json")
    
    if sample_file.exists() and not full_file.exists():
        print("💡 Found sample file. Upload sample (10 records) first? [y/n]")
        choice = input("> ").strip().lower()
        
        if choice == 'y':
            data_file = "mtsamples_sample_10.json"
        else:
            print("❌ Full dataset not found. Run 'python download_mtsamples.py' first")
            return
    elif full_file.exists():
        print("💡 Upload full dataset or sample?")
        print("  1. Sample (10 records) - Quick test")
        print("  2. Full dataset (5000+ records) - Production")
        choice = input("> ").strip()
        
        data_file = "mtsamples_sample_10.json" if choice == "1" else "mtsamples_cipercare.json"
    else:
        print("❌ No data files found. Run 'python download_mtsamples.py' first")
        return
    
    # Load data
    patients = load_mtsamples_data(data_file)
    
    if not patients:
        return
    
    # Create embeddings
    patients = create_embeddings(patients)
    
    # Upload to CyborgDB
    upload_to_cyborgdb(patients)
    
    # Test query
    print("\n" + "="*60)
    print("🧪 TESTING QUERIES")
    print("="*60)
    
    db = CyborgLiteManager()
    
    test_queries = [
        "cardiovascular disease",
        "diabetes management",
        "orthopedic surgery",
        "discharge summary"
    ]
    
    for query in test_queries:
        test_query(db, query)
    
    print("\n✅ ALL DONE!")
    print("="*60)
    print("You can now query your chatbot with clinical questions!")
    print("="*60)


if __name__ == "__main__":
    main()
