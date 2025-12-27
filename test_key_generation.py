import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("CYBORGDB_API_KEY")
print(f"API Key from env: {api_key}")
print(f"API Key length: {len(api_key)}")

combined = f"{api_key}:patient_embeddings"
index_key = hashlib.sha256(combined.encode()).digest()
print(f"\nComputed key: {index_key.hex()}")
print(f"Key length: {len(index_key)}")
