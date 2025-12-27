"""
Check what's actually in the patient_records collection
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.cyborg_lite_manager import get_cyborg_manager

def check_collection():
    print("\n=== Checking patient_records collection ===\n")
    
    manager = get_cyborg_manager()
    
    # Try to get the index
    try:
        index = manager.get_index("patient_records")
        print(f"✅ Index 'patient_records' found")
        
        # Try a search without patient filter to see what's there
        zero_embedding = [0.01] * 768
        results = index.query(query_vectors=[zero_embedding], top_k=10)
        
        print(f"\n📊 Found {len(results)} records")
        
        if results:
            print("\nFirst 3 records:")
            for i, result in enumerate(results[:3]):
                print(f"\n--- Record {i+1} ---")
                print(f"ID: {result.get('id', 'N/A')}")
                print(f"Distance: {result.get('distance', 'N/A')}")
                metadata = result.get('metadata', {})
                print(f"Metadata keys: {list(metadata.keys())}")
                print(f"Patient ID: {metadata.get('patient_id', 'MISSING')}")
                print(f"Gender: {metadata.get('gender', 'N/A')}")
                print(f"Birth Date: {metadata.get('birth_date', 'N/A')}")
                print(f"Data Source: {metadata.get('data_source', 'N/A')}")
        else:
            print("⚠️ No records found in collection")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_collection()
