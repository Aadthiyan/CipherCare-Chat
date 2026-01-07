"""
Check if patient data exists in CyborgDB
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 Checking CyborgDB Data Status")
print("=" * 70)

# Get configuration
CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")

print(f"\nCyborgDB URL: {CYBORGDB_URL}")
print(f"API Key: {'✓ Set' if CYBORGDB_API_KEY else '✗ Missing'}")

if not CYBORGDB_API_KEY:
    print("\n✗ CYBORGDB_API_KEY not found in .env")
    sys.exit(1)

# Try to use the SDK to check data
try:
    print("\n1. Initializing CyborgDB client...")
    import cyborgdb
    
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    print("   ✓ Client initialized")
    
    # Try to load index
    print("\n2. Checking for patient data index...")
    index_names = ["patient_records_v1", "patient_data_v2", "patient_data_FINAL"]
    
    found_index = None
    for index_name in index_names:
        try:
            # Try to get index stats
            print(f"   Checking '{index_name}'...")
            
            # Create deterministic key
            import hashlib
            combined = f"{CYBORGDB_API_KEY}:{index_name}"
            index_key = hashlib.sha256(combined.encode()).digest()
            
            # Try to load
            index = client.load_index(
                index_name=index_name,
                index_key=index_key
            )
            
            # Try a test query to see if there's data
            test_vec = [0.0] * 768  # Zero vector
            results = index.query(query_vectors=[test_vec], top_k=5)
            
            if results and len(results) > 0:
                print(f"   ✓ Found index '{index_name}' with {len(results)} sample records")
                found_index = index_name
                
                # Show sample record
                if results[0]:
                    sample = results[0]
                    print(f"\n   Sample record:")
                    print(f"   - ID: {sample.get('id', 'N/A')}")
                    print(f"   - Patient ID: {sample.get('metadata', {}).get('patient_id', 'N/A')}")
                    print(f"   - Record Type: {sample.get('metadata', {}).get('record_type', 'N/A')}")
                break
            else:
                print(f"   ⚠ Index '{index_name}' exists but appears empty")
                
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not found" in error_msg:
                print(f"   ✗ Index '{index_name}' not found")
            else:
                print(f"   ⚠ Error checking '{index_name}': {str(e)[:80]}")
    
    if found_index:
        print(f"\n✅ SUCCESS: Found patient data in index '{found_index}'")
        print("\nYour CyborgDB has data and should work for queries!")
    else:
        print("\n⚠️  WARNING: No patient data found in any index")
        print("\nYou need to upload data:")
        print("   python upload_to_render.py")
        
except ImportError:
    print("\n✗ cyborgdb package not installed")
    print("   Install with: pip install cyborgdb")
    sys.exit(1)
    
except ConnectionError as e:
    print(f"\n✗ Connection failed: {str(e)[:100]}")
    print("\nPossible causes:")
    print("   1. CyborgDB service is not running")
    print("   2. Wrong CYBORGDB_BASE_URL in .env")
    print("   3. Network/firewall blocking connection")
    print("\nTry:")
    print("   python diagnose_cyborgdb.py")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Error: {str(e)[:200]}")
    print("\nRun diagnostic for more details:")
    print("   python diagnose_cyborgdb.py")
    sys.exit(1)

print("\n" + "=" * 70)
