"""
Quick script to delete old collection and upload fresh data
"""

import cyborgdb
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

client = cyborgdb.Client(
    api_key=os.getenv("CYBORGDB_API_KEY"),
    base_url=os.getenv("CYBORGDB_BASE_URL")
)

# Delete old collection
print("Deleting old patient_data_v2 collection...")
try:
    api_key = os.getenv("CYBORGDB_API_KEY", "default")
    combined = f"{api_key}:patient_data_v2"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    from cyborgdb.openapi_client.models import IndexOperationRequest
    client.api.delete_index_v1_indexes_delete_post(
        index_operation_request=IndexOperationRequest(
            index_name="patient_data_v2",
            index_key=index_key
        )
    )
    print("✓ Deleted old collection")
except Exception as e:
    print(f"Note: {e}")

print("\n✓ Ready to upload fresh data!")
print("\nNow run:")
print("  1. python parse_preprocessed_synthea.py  (if not done)")
print("  2. Update upload_structured_data.py to use 'synthea_structured_FIXED.json'")
print("  3. python upload_structured_data.py")
