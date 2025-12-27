"""
Script to DELETE the patient_data_v2 index entirely.
This clears all data (good and bad) to start fresh.
"""

import cyborgdb
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

def delete_data():
    client = cyborgdb.Client(
        api_key=os.getenv("CYBORGDB_API_KEY"),
        base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
    )

    index_name = "patient_data_v2"
    
    # Generate deterministic key
    api_key = os.getenv("CYBORGDB_API_KEY", "default")
    combined = f"{api_key}:{index_name}"
    index_key = hashlib.sha256(combined.encode()).digest()

    print(f"Deleting index: {index_name}...")
    try:
        # Use the SDK's delete_index method
        client.delete_index(
            index_name=index_name,
            index_key=index_key
        )
        print(f"✓ Successfully deleted '{index_name}'")
    except Exception as e:
        print(f"Index deletion status: {e}")
        # Sometimes it says 'Internal Error' if index doesn't exist, which is fine
        
    # Verify
    indexes = client.list_indexes()
    print(f"Current indexes: {indexes}")

if __name__ == "__main__":
    delete_data()
