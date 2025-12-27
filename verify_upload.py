"""
Check if uploaded data has proper LOINC codes
"""

import cyborgdb
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

client = cyborgdb.Client(
    api_key=os.getenv('CYBORGDB_API_KEY'),
    base_url=os.getenv('CYBORGDB_BASE_URL')
)

# Load index
api_key = os.getenv('CYBORGDB_API_KEY', 'default')
combined = f'{api_key}:patient_data_v2'
index_key = hashlib.sha256(combined.encode()).digest()
index = client.load_index(index_name='patient_data_v2', index_key=index_key)

# Query
results = index.query(query_vectors=[[0.0]*768], top_k=10)

print("Sample records from database:")
print("="*70)

for i, r in enumerate(results[:5], 1):
    meta = r.get('metadata', {})
    print(f"\n{i}. Record Type: {meta.get('record_type', 'N/A')}")
    print(f"   Patient: {meta.get('patient_id', 'N/A')}")
    print(f"   Display: {meta.get('display', 'N/A')}")
    print(f"   LOINC: {meta.get('loinc_code', 'N/A')}")
    print(f"   Value: {meta.get('value', 'N/A')} {meta.get('unit', '')}")
    print(f"   Date: {meta.get('effective_date', 'N/A')}")

print("\n" + "="*70)
print("✓ Check complete!")
