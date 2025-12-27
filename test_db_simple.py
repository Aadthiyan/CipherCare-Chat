"""
Simple test to verify PID-131 data in database
"""
from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()

print("Testing database for PID-131...")
db = CyborgLiteManager()

# Create a dummy query vector (all zeros is fine for testing)
dummy_vec = [0.0] * 768

# Search WITHOUT patient filter first
print("\n1. Searching without patient filter...")
results_all = db.search(dummy_vec, k=5, collection="patient_data_FINAL")
print(f"   Found {len(results_all)} total results")
if results_all:
    patient_ids = [r.get('metadata', {}).get('patient_id', 'NO_ID') for r in results_all]
    print(f"   Patient IDs: {patient_ids}")

# Search WITH PID-131 filter
print("\n2. Searching WITH PID-131 filter...")
results_131 = db.search(dummy_vec, k=10, patient_id="PID-131", collection="patient_data_FINAL")
print(f"   Found {len(results_131)} results for PID-131")
if results_131:
    print(f"   First result metadata: {results_131[0].get('metadata', {})}")
else:
    print("   NO RESULTS - This is the problem!")

print("\nDone.")
