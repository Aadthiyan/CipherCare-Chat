"""
Test query to retrieve patient details from CyborgDB
"""

import os
from dotenv import load_dotenv
from backend.cyborg_lite_manager import CyborgLiteManager
from sentence_transformers import SentenceTransformer

load_dotenv()

# Initialize
embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
db = CyborgLiteManager()

# Test patient ID
patient_id = "PID-102"

print(f"Searching for patient: {patient_id}")
print("="*70)

# Create a query for this patient's data
query_text = f"patient {patient_id} medical records vitals conditions medications"
query_embedding = embedder.encode(query_text).tolist()

# Search in the new collection
results = db.search(
    query_vec=query_embedding,
    k=50,  # Get up to 50 records
    patient_id=patient_id,  # Filter by patient ID
    collection="patient_data_v2"
)

print(f"\nFound {len(results)} records for {patient_id}:\n")

# Group by record type
by_type = {}
for result in results:
    metadata = result.get('metadata', {})
    record_type = metadata.get('record_type', 'unknown')
    
    if record_type not in by_type:
        by_type[record_type] = []
    by_type[record_type].append(metadata)

# Display summary
print("SUMMARY:")
print("-" * 70)
for rtype, records in sorted(by_type.items()):
    print(f"{rtype.upper()}: {len(records)} records")

# Show sample records
print("\n" + "="*70)
print("SAMPLE RECORDS:")
print("="*70)

for rtype, records in sorted(by_type.items()):
    print(f"\n{rtype.upper()} ({len(records)} total):")
    print("-" * 70)
    
    # Show first 3 records of each type
    for i, record in enumerate(records[:3], 1):
        print(f"\n{i}. {record.get('display', 'N/A')}")
        
        if rtype == 'observation':
            value = record.get('value')
            unit = record.get('unit', '')
            loinc = record.get('loinc_code', 'N/A')
            print(f"   Value: {value} {unit}")
            print(f"   LOINC: {loinc}")
            print(f"   Date: {record.get('effective_date', 'N/A')}")
        
        elif rtype == 'condition':
            snomed = record.get('snomed_code', 'N/A')
            status = record.get('status', 'N/A')
            print(f"   SNOMED: {snomed}")
            print(f"   Status: {status}")
            print(f"   Onset: {record.get('effective_date', 'N/A')}")
        
        elif rtype == 'medication':
            rxnorm = record.get('rxnorm_code', 'N/A')
            status = record.get('status', 'N/A')
            print(f"   RxNorm: {rxnorm}")
            print(f"   Status: {status}")
            print(f"   Start: {record.get('effective_date', 'N/A')}")

print("\n" + "="*70)
print("✓ Query complete!")
print("="*70)
