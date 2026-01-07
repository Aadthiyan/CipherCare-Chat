"""
Test if data exists in CyborgDB by attempting a simple query
"""

import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print("=" * 70)
print("🔍 Testing CyborgDB Data Existence")
print("=" * 70)
print(f"\nURL: {CYBORGDB_URL}")
print(f"API Key: {CYBORGDB_API_KEY[:20]}...")

try:
    import cyborgdb
    
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    
    index_name = "patient_records_v1"
    combined = f"{CYBORGDB_API_KEY}:{index_name}"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    print(f"\n📊 Loading index: {index_name}")
    
    try:
        index = client.load_index(
            index_name=index_name,
            index_key=index_key
        )
        print(f"✓ Index loaded successfully")
        
        # Try to query with a zero vector
        print(f"\n🔍 Attempting to query for records...")
        zero_vec = [0.0] * 768
        results = index.query(query_vectors=[zero_vec], top_k=10)
        
        if results and len(results) > 0:
            print(f"\n✅ SUCCESS! Found {len(results)} records!")
            print(f"\nSample record:")
            print(f"  ID: {results[0].get('id')}")
            print(f"  Patient: {results[0].get('metadata', {}).get('patient_id')}")
            print(f"  Type: {results[0].get('metadata', {}).get('record_type')}")
            print(f"\n🎉 Your data is accessible!")
        else:
            print(f"\n❌ PROBLEM: Index exists but contains NO DATA!")
            print(f"\n💡 This means:")
            print(f"   - CyborgDB service restarted (data lost)")
            print(f"   - Free tier uses ephemeral Redis (no persistence)")
            print(f"\n🔧 Solution:")
            print(f"   Re-upload data: python upload_sdk_fast.py (option 5)")
            print(f"   Takes ~33 minutes")
            
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower():
            print(f"\n❌ Index '{index_name}' does not exist")
            print(f"\n💡 CyborgDB was completely reset")
            print(f"\n🔧 Solution:")
            print(f"   Upload data: python upload_sdk_fast.py (option 5)")
        else:
            print(f"\n⚠️  Error: {error_msg}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
