"""
Simple test - just try to query CyborgDB without uploading
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print("Testing CyborgDB query...")
print(f"URL: {CYBORGDB_URL}")

try:
    import cyborgdb
    import hashlib
    
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    
    # Try to load the index that should exist
    index_name = "patient_records_v1"
    combined = f"{CYBORGDB_API_KEY}:{index_name}"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    print(f"\nTrying to load index: {index_name}")
    
    try:
        index = client.load_index(
            index_name=index_name,
            index_key=index_key
        )
        print("✓ Index loaded!")
        
        # Try a simple query
        print("\nTrying query...")
        zero_vec = [0.0] * 768
        results = index.query(query_vectors=[zero_vec], top_k=3)
        
        if results:
            print(f"✓ Found {len(results)} results!")
            for i, r in enumerate(results[:3]):
                print(f"\n  Result {i+1}:")
                print(f"    ID: {r.get('id')}")
                print(f"    Patient: {r.get('metadata', {}).get('patient_id')}")
        else:
            print("⚠ Index exists but no data found")
            print("\nYou need to upload data:")
            print("  python upload_to_render.py")
            
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"✗ Index '{index_name}' does not exist")
            print("\nYou need to upload data first:")
            print("  python upload_to_render.py")
        else:
            raise
            
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
