import cyborgdb
import os
import secrets
import json
from dotenv import load_dotenv

load_dotenv()

client = cyborgdb.Client(
    api_key=os.getenv("CYBORGDB_API_KEY"),
    base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
)

# Load the index
import hashlib
api_key = os.getenv("CYBORGDB_API_KEY", "default")
combined = f"{api_key}:patient_embeddings"
index_key = hashlib.sha256(combined.encode()).digest()

index = client.load_index(index_name="patient_embeddings", index_key=index_key)

# Create a test query vector (all zeros for simplicity)
query_vec = [0.0] * 768

# Query
results = index.query(query_vectors=[query_vec], top_k=3)

print("Query results type:", type(results))
print("Query results length:", len(results) if isinstance(results, list) else "N/A")
print("\nFirst element type:", type(results[0]) if results else "N/A")
print("First element:", results[0] if results else "N/A")

if results and len(results) > 0:
    print(f"\nDetailed view of first result:")
    print(f"  Type: {type(results[0])}")
    print(f"  Content: {json.dumps(results[0] if isinstance(results[0], (dict, list)) else str(results[0]), indent=2, default=str)}")
