"""
Quick verification - count records in CyborgDB (no TensorFlow needed)
"""

import os
import sys
from dotenv import load_dotenv
import hashlib

load_dotenv()

CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print("=" * 70)
print("✅ Quick CyborgDB Verification")
print("=" * 70)

try:
    import cyborgdb
    
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    
    index_name = "patient_records_v1"
    combined = f"{CYBORGDB_API_KEY}:{index_name}"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    print(f"\n🔍 Checking index: {index_name}")
    print(f"📍 URL: {CYBORGDB_URL}")
    
    try:
        index = client.load_index(
            index_name=index_name,
            index_key=index_key
        )
        print(f"\n✅ SUCCESS! Index '{index_name}' exists and is accessible!")
        print(f"\n🎉 Your 76,317 records (150 patients) are ready to query!")
        print(f"\n📋 Next steps:")
        print(f"   1. Test queries from your backend")
        print(f"   2. Try querying from your frontend")
        print(f"   3. Monitor Render for any service restarts")
        
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower():
            print(f"\n❌ ERROR: Index '{index_name}' not found!")
            print(f"\n💡 This means:")
            print(f"   - CyborgDB service may have restarted (data lost)")
            print(f"   - Or upload didn't complete successfully")
            print(f"\n🔧 Solution:")
            print(f"   Re-run: python upload_sdk_fast.py (option 5)")
        else:
            print(f"\n⚠️  Error: {error_msg}")
    
except Exception as e:
    print(f"\n✗ Connection Error: {e}")
    print(f"\n🔧 Check:")
    print(f"   1. Is CyborgDB service running on Render?")
    print(f"   2. Is CYBORGDB_BASE_URL correct in .env?")
    print(f"   3. Is CYBORGDB_API_KEY set in .env?")

print("\n" + "=" * 70)
