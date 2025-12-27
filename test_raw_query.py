import cyborgdb
import os
import json
import hashlib
from dotenv import load_dotenv

load_dotenv()

client = cyborgdb.Client(
    api_key=os.getenv("CYBORGDB_API_KEY"),
    base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
)

# Load the index with deterministic key
api_key = os.getenv("CYBORGDB_API_KEY")
combined = f"{api_key}:patient_embeddings"
index_key = hashlib.sha256(combined.encode()).digest()

index = client.load_index(index_name="patient_embeddings", index_key=index_key)

# Create a test query vector (all zeros)
query_vec = [0.0] * 768

# Query
results = index.query(query_vectors=[query_vec], top_k=3)

print("Results type:", type(results))
print("Results length:", len(results) if isinstance(results, list) else "N/A")
print("\nFull results:")
print(json.dumps(results, indent=2, default=str))

if results and len(results) > 0:
    print(f"\n\nFirst element type: {type(results[0])}")
    print(f"First element is dict: {isinstance(results[0], dict)}")
    if isinstance(results[0], dict):
        print(f"First element keys: {list(results[0].keys())}")
    print(f"First element content:\n{json.dumps(results[0], indent=2, default=str)}")
