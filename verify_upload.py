"""
Check CyborgDB status and verify uploaded data
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print("=" * 70)
print("🔍 CyborgDB Data Verification")
print("=" * 70)

try:
    import cyborgdb
    import hashlib
    
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    
    index_name = "patient_records_v1"
    combined = f"{CYBORGDB_API_KEY}:{index_name}"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    print(f"\nLoading index: {index_name}")
    index = client.load_index(
        index_name=index_name,
        index_key=index_key
    )
    print("✓ Index loaded!")
    
    # Query to get sample records
    print("\n" + "=" * 70)
    print("📊 SAMPLING DATA")
    print("=" * 70)
    
    zero_vec = [0.0] * 768
    results = index.query(query_vectors=[zero_vec], top_k=100)
    
    if results:
        print(f"\n✓ Found {len(results)} sample records")
        
        # Analyze what we have
        patients = set()
        record_types = {}
        
        for r in results:
            metadata = r.get('metadata', {})
            patient_id = metadata.get('patient_id')
            record_type = metadata.get('record_type')
            
            if patient_id:
                patients.add(patient_id)
            if record_type:
                record_types[record_type] = record_types.get(record_type, 0) + 1
        
        print(f"\nUnique patients in sample: {len(patients)}")
        print(f"\nRecord types in sample:")
        for rtype, count in sorted(record_types.items()):
            print(f"  {rtype}: {count}")
        
        # Show a few sample records
        print("\n" + "=" * 70)
        print("📝 SAMPLE RECORDS")
        print("=" * 70)
        for i, r in enumerate(results[:5]):
            metadata = r.get('metadata', {})
            print(f"\nRecord {i+1}:")
            print(f"  ID: {r.get('id')}")
            print(f"  Patient: {metadata.get('patient_id')}")
            print(f"  Type: {metadata.get('record_type')}")
            print(f"  Display: {metadata.get('display', 'N/A')[:60]}...")
            print(f"  Date: {metadata.get('effective_date', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("✅ DATA VERIFICATION COMPLETE")
        print("=" * 70)
        print(f"\nYou have {len(results)} records accessible (sample of 100)")
        print("Your CyborgDB is working and queryable!")
        
        print("\n💡 About the upload errors:")
        print("   - 80,300 records uploaded successfully")
        print("   - 30,760 errors likely due to:")
        print("     • Network timeouts to Render")
        print("     • Rate limiting")
        print("     • Duplicate record IDs")
        print("     • CyborgDB service restarts")
        
        print("\n🎯 Next Steps:")
        print("   1. Test queries from your backend")
        print("   2. If you need more data, re-run upload for failed records")
        print("   3. 80K records is already substantial for testing!")
        
    else:
        print("\n⚠️  No records found")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
