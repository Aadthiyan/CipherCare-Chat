"""
Debug search exactly as backend does it
"""

import os
from dotenv import load_dotenv
from backend.cyborg_lite_manager import CyborgLiteManager
from sentence_transformers import SentenceTransformer

load_dotenv()

def debug_search():
    print("Initializing Manager...")
    db = CyborgLiteManager()
    
    print("\nInitializing Embedder (to match backend)...")
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    
    # Generate vector for "glucose"
    query = "glucose level"
    print(f"\nQuerying for: '{query}'")
    query_vec = embedder.encode(query).tolist()
    
    # Search for PID-101
    patient_id = "PID-101"
    print(f"Filter: patient_id='{patient_id}'")
    
    try:
        results = db.search(
            query_vec=query_vec,
            k=5, 
            patient_id=patient_id,
            collection="patient_data_v2"
        )
        
        print(f"\nFound {len(results)} results:")
        for i, res in enumerate(results, 1):
            meta = res.get('metadata', {})
            print(f"\nResult {i}:")
            print(f"  Score: {res.get('score', 0):.4f}")
            print(f"  Display: {meta.get('display', 'N/A')}")
            print(f"  LOINC: {meta.get('loinc_code', 'N/A')}")
            print(f"  Value: {meta.get('value', 'N/A')} {meta.get('unit', '')}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_search()
