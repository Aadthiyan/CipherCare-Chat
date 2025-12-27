"""Test query for PID-102 after enrichment to confirm sources and answer."""
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def main():
    # Login
    login_url = "http://127.0.0.1:8000/auth/login"
    login_data = {
        "username": "jsmith",
        "password": "Aadhithiyan@99"
    }
    
    print("🔐 Logging in...")
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    tokens = login_response.json()
    access_token = tokens.get("access_token")
    print(f"✅ Login successful")
    
    # Query PID-102
    print("\n📊 Querying PID-102 with enriched data...")
    query_url = "http://127.0.0.1:8000/api/v1/query"
    query_data = {
        "patient_id": "PID-102",
        "question": "What are the patient's diagnoses and current medications?",
        "retrieve_k": 10
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    query_response = requests.post(query_url, json=query_data, headers=headers)
    print(f"Status Code: {query_response.status_code}")
    
    if query_response.status_code == 200:
        result = query_response.json()
        print(f"\n✅ Query successful!")
        print(f"\n📝 Answer:\n{result.get('answer', 'N/A')}")
        print(f"\n📚 Number of sources: {len(result.get('sources', []))}")
        if result.get('sources'):
            print("\nFirst 3 sources:")
            for i, src in enumerate(result.get('sources', [])[:3]):
                print(f"  {i+1}. Type={src.get('type')}, Date={src.get('date')}")
    else:
        print(f"❌ Query failed: {query_response.text}")

if __name__ == "__main__":
    main()
