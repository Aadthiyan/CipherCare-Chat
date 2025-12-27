import cyborgdb
import os
import hashlib
from dotenv import load_dotenv
from cyborgdb.openapi_client.models import IndexOperationRequest

load_dotenv()

client = cyborgdb.Client(
    api_key=os.getenv("CYBORGDB_API_KEY"),
    base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
)

# List all indexes
print("Listing all indexes...")
indexes = client.list_indexes()
print(f"Found indexes: {indexes}\n")

# Delete the patient_embeddings index to start fresh
if "patient_embeddings" in indexes:
    print("Deleting old patient_embeddings index...")
    try:
        # Generate the same deterministic key used when creating the index
        api_key = os.getenv("CYBORGDB_API_KEY", "default")
        combined = f"{api_key}:patient_embeddings"
        index_key = hashlib.sha256(combined.encode()).digest()
        
        response = client.api.delete_index_v1_indexes_delete_post(
            index_operation_request=IndexOperationRequest(
                index_name="patient_embeddings",
                index_key=index_key
            )
        )
        print(f"Successfully deleted index!\n")
    except Exception as e:
        print(f"Error: {e}\n")

# Verify it's gone
indexes = client.list_indexes()
print(f"Remaining indexes: {indexes}")
