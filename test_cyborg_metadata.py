"""Direct test of CyborgDB metadata retrieval"""
from backend.cyborg_lite_manager import CyborgLiteManager
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

db = CyborgLiteManager()
embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# Query for PID-102 observations
query_vec = embedder.encode("blood pressure glucose weight").tolist()
results = db.search(
    query_vec,
    k=10,
    patient_id="PID-102",
    collection="patient_data_FINAL"
)

print(f"Found {len(results)} results for PID-102")
print("\nFirst 3 results:")
for i, result in enumerate(results[:3]):
    metadata = result.get('metadata', {})
    print(f"\nResult {i+1}:")
    print(f"  Record Type: {metadata.get('record_type')}")
    print(f"  Display: {metadata.get('display')}")
    print(f"  Value: {metadata.get('value')}")
    print(f"  Unit: {metadata.get('unit')}")
    print(f"  Date: {metadata.get('effective_date')}")
    print(f"  All metadata keys: {list(metadata.keys())}")
