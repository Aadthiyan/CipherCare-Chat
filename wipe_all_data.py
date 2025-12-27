"""
WIPE ALL DATA
Deletes ALL indexes from CyborgDB to ensure a completely clean slate.
"""

import cyborgdb
import os
import hashlib
from dotenv import load_dotenv
from cyborgdb.openapi_client.models import IndexOperationRequest

load_dotenv()

def wipe_all():
    print("="*70)
    print("WIPING ALL CYBORGDB DATA")
    print("="*70)
    
    client = cyborgdb.Client(
        api_key=os.getenv("CYBORGDB_API_KEY"),
        base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
    )

    try:
        indexes = client.list_indexes()
        print(f"Found indexes: {indexes}")
        
        if not indexes:
            print("✓ No indexes found. System is clean.")
            return

        for index_name in indexes:
            print(f"Deleting '{index_name}'...")
            
            # Generate key
            api_key = os.getenv("CYBORGDB_API_KEY", "default")
            combined = f"{api_key}:{index_name}"
            index_key = hashlib.sha256(combined.encode()).digest()
            
            try:
                # Try standard delete
                client.delete_index(
                    index_name=index_name,
                    index_key=index_key
                )
                print(f"✓ Deleted '{index_name}'")
            except Exception as e:
                print(f"  Standard delete failed: {e}")
                # Try API direct delete as fallback
                try:
                    client.api.delete_index_v1_indexes_delete_post(
                        index_operation_request=IndexOperationRequest(
                            index_name=index_name,
                            index_key=index_key
                        )
                    )
                    print(f"✓ Deleted '{index_name}' (via API)")
                except Exception as e2:
                    print(f"  ❌ Force delete failed: {e2}")

        # Final Verify
        remaining = client.list_indexes()
        if not remaining:
            print("\n✓ SUCCESS: All data wiped.")
        else:
            print(f"\n❌ WARNING: Some indexes remain: {remaining}")

    except Exception as e:
        print(f"Error accessing CyborgDB: {e}")

if __name__ == "__main__":
    wipe_all()
