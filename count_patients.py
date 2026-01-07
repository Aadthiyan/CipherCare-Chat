"""
Count unique patients in CyborgDB
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print("=" * 70)
print("🔍 Counting Patients in CyborgDB")
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
    
    print(f"\nLoading index: {index_name}...")
    index = client.load_index(
        index_name=index_name,
        index_key=index_key
    )
    print("✓ Index loaded!")
    
    # Query large sample to count patients
    print("\n🔍 Sampling records to count patients...")
    print("   (This may take a minute...)")
    
    zero_vec = [0.0] * 768
    
    # Try to get as many records as possible
    # CyborgDB might limit results, so we'll sample
    results = index.query(query_vectors=[zero_vec], top_k=10000)
    
    if results:
        print(f"\n✓ Retrieved {len(results)} sample records")
        
        # Count unique patients
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
        
        print("\n" + "=" * 70)
        print("📊 PATIENT COUNT RESULTS")
        print("=" * 70)
        
        print(f"\n✅ Unique patients found: {len(patients)}")
        print(f"📝 Sample size: {len(results)} records")
        
        print(f"\n📋 Record types in sample:")
        for rtype, count in sorted(record_types.items()):
            print(f"   {rtype}: {count}")
        
        # Estimate total patients
        if len(results) == 10000:
            print(f"\n⚠️  Note: Sample limited to 10,000 records")
            print(f"   Actual patient count may be higher")
            print(f"   Estimated total: {len(patients)} - {len(patients) * 2} patients")
        else:
            print(f"\n✅ Complete dataset sampled")
            print(f"   Total patients: {len(patients)}")
        
        # Show some patient IDs
        print(f"\n👥 Sample patient IDs:")
        for i, pid in enumerate(sorted(list(patients))[:10]):
            print(f"   {i+1}. {pid}")
        if len(patients) > 10:
            print(f"   ... and {len(patients) - 10} more")
        
        # Calculate average records per patient
        avg_records = len(results) / len(patients) if len(patients) > 0 else 0
        print(f"\n📊 Average records per patient: {avg_records:.1f}")
        
        # Estimate total records
        if len(results) == 10000:
            estimated_total = len(patients) * avg_records
            print(f"📈 Estimated total records: {estimated_total:.0f}")
        
    else:
        print("\n⚠️  No records found in CyborgDB")
        print("   The upload may have failed or data was lost")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
