"""Check if PID-131 exists in uploaded data"""
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()

db = CyborgLiteManager()
index = db.get_index('patient_data_FINAL')

# Get a large sample and check for PID-131
dummy_vec = [0.0] * 768
results = index.query(query_vectors=[dummy_vec], top_k=1000)

patient_ids = [r['metadata'].get('patient_id') for r in results if 'metadata' in r]
unique_patients = sorted(set(patient_ids))

print(f"Total results retrieved: {len(results)}")
print(f"Unique patients in sample: {len(unique_patients)}")
print(f"First 20 patients: {unique_patients[:20]}")
print(f"\nPID-131 in results: {'PID-131' in patient_ids}")

if 'PID-131' in patient_ids:
    count_131 = patient_ids.count('PID-131')
    print(f"PID-131 appears {count_131} times in the sample")
