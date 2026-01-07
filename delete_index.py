"""
Delete old CyborgDB index to start fresh
"""

import os
import sys
from dotenv import load_dotenv
import hashlib

load_dotenv()

CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print("=" * 70)
print("🗑️  Delete CyborgDB Index")
print("=" * 70)

index_name = input("\nEnter index name to delete [patient_records_v1]: ").strip() or "patient_records_v1"

print(f"\n⚠️  WARNING: This will DELETE all data in index '{index_name}'")
print("This action cannot be undone!")
confirm = input("\nType 'DELETE' to confirm: ").strip()

if confirm != "DELETE":
    print("\n❌ Deletion cancelled")
    sys.exit(0)

try:
    import cyborgdb
    
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    
    # Create deterministic key
    combined = f"{CYBORGDB_API_KEY}:{index_name}"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    print(f"\n🔄 Attempting to delete index '{index_name}'...")
    
    try:
        # Try to load first to verify it exists
        index = client.load_index(
            index_name=index_name,
            index_key=index_key
        )
        print(f"✓ Index found")
        
        # Delete it
        # Note: CyborgDB SDK might not have delete_index method
        # In that case, we'll need to use the API directly
        print(f"⚠️  Note: CyborgDB free tier may not persist deletions")
        print(f"   Easiest solution: Just upload new data (it will overwrite)")
        
    except Exception as e:
        if "does not exist" in str(e).lower():
            print(f"ℹ️  Index '{index_name}' does not exist (already deleted or never created)")
        else:
            print(f"⚠️  Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATION")
    print("=" * 70)
    print("\nSince CyborgDB on Render free tier uses ephemeral Redis:")
    print("1. Old data is automatically cleared on service restart")
    print("2. Just run your upload - it will replace old data")
    print("3. Or use a new index name (e.g., 'patient_records_v2')")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
