from backend.cyborg_lite_manager import CyborgLiteManager
from dotenv import load_dotenv

load_dotenv()

db = CyborgLiteManager()
index = db.get_index('patient_data_FINAL')

# Query for PID-131 specifically
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

query_vec = embedder.encode("patient records").tolist()

# Search for PID-131
results = db.search(query_vec, k=10, patient_id="PID-131", collection="patient_data_FINAL")

print(f"Found {len(results)} results for PID-131")
if results:
    print("Sample result:")
    print(results[0])
else:
    print("No results found. Checking if ANY data exists...")
    # Try without patient filter
    all_results = db.search(query_vec, k=5, collection="patient_data_FINAL")
    print(f"Total results without filter: {len(all_results)}")
    if all_results:
        print(f"Sample patient IDs: {[r.get('metadata', {}).get('patient_id') for r in all_results[:5]]}")
