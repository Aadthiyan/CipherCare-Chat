"""
Test CyborgDB connection and upload a single test record
"""

import os
import sys
from dotenv import load_dotenv
import requests

load_dotenv()

CYBORGDB_URL = os.getenv("CYBORGDB_BASE_URL", "https://cyborgdb-toj5.onrender.com")
CYBORGDB_API_KEY = os.getenv("CYBORGDB_API_KEY")
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

print("=" * 70)
print("🧪 Testing CyborgDB Connection & Upload")
print("=" * 70)

print(f"\nCyborgDB URL: {CYBORGDB_URL}")
print(f"API Key: {'✓ Set' if CYBORGDB_API_KEY else '✗ Missing'}")
print(f"HF Token: {'✓ Set' if HF_API_TOKEN else '✗ Missing'}")

if not CYBORGDB_API_KEY:
    print("\n✗ CYBORGDB_API_KEY not set")
    sys.exit(1)

if not HF_API_TOKEN:
    print("\n✗ HUGGINGFACE_API_KEY not set")
    sys.exit(1)

# Test 1: Try to use the Python SDK
print("\n" + "=" * 70)
print("Test 1: Using CyborgDB Python SDK")
print("=" * 70)

try:
    import cyborgdb
    import hashlib
    
    print("\n1. Initializing client...")
    client = cyborgdb.Client(
        api_key=CYBORGDB_API_KEY,
        base_url=CYBORGDB_URL
    )
    print("   ✓ Client initialized")
    
    # Create test index
    print("\n2. Creating/loading test index...")
    index_name = "test_patient_records"
    combined = f"{CYBORGDB_API_KEY}:{index_name}"
    index_key = hashlib.sha256(combined.encode()).digest()
    
    try:
        index = client.create_index(
            index_name=index_name,
            index_key=index_key
        )
        print(f"   ✓ Created new index '{index_name}'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"   ℹ Index already exists, loading...")
            index = client.load_index(
                index_name=index_name,
                index_key=index_key
            )
            print(f"   ✓ Loaded existing index '{index_name}'")
        else:
            raise
    
    # Create a test embedding using HF API
    print("\n3. Creating test embedding...")
    hf_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-mpnet-base-v2"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    test_text = "Patient John Doe, age 45, diagnosed with hypertension"
    response = requests.post(hf_url, headers=headers, json={"inputs": test_text})
    
    if response.status_code == 200:
        embedding = response.json()
        print(f"   ✓ Created embedding (dim: {len(embedding)})")
    else:
        print(f"   ✗ HF API error: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        sys.exit(1)
    
    # Upload test record
    print("\n4. Uploading test record...")
    test_record = {
        "id": "test_record_001",
        "vector": embedding,
        "metadata": {
            "patient_id": "TEST_P001",
            "record_type": "test_record",
            "text_summary": test_text,
            "display": "Test Patient Record",
            "effective_date": "2026-01-07",
            "status": "test"
        }
    }
    
    index.upsert([test_record])
    print("   ✓ Test record uploaded successfully!")
    
    # Query to verify
    print("\n5. Querying to verify upload...")
    results = index.query(query_vectors=[embedding], top_k=1)
    
    if results and len(results) > 0:
        print(f"   ✓ Query successful! Found {len(results)} result(s)")
        print(f"\n   Sample result:")
        print(f"   - ID: {results[0].get('id')}")
        print(f"   - Patient ID: {results[0].get('metadata', {}).get('patient_id')}")
        print(f"   - Text: {results[0].get('metadata', {}).get('text_summary', '')[:50]}...")
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! CyborgDB is working correctly!")
        print("=" * 70)
        print("\nYou can now upload your full patient dataset:")
        print("   python upload_to_render.py")
        
    else:
        print("   ⚠ Query returned no results")
        print("   This might indicate an issue with the upload")
    
except ImportError:
    print("\n✗ cyborgdb package not installed")
    print("   Install with: pip install cyborgdb")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("❌ FAILED - CyborgDB connection issue")
    print("=" * 70)
    print("\nPossible causes:")
    print("1. Service is running but not accepting SDK connections")
    print("2. Wrong API key or base URL")
    print("3. Network/firewall issue")
    print("4. Service needs to be restarted")
    
    print("\nTry:")
    print("1. Check Render logs for errors")
    print("2. Verify CYBORGDB_API_KEY matches in Render env vars")
    print("3. Restart the CyborgDB service on Render")
    sys.exit(1)

print("\n" + "=" * 70)
