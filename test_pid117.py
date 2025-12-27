"""Test query with PID-117"""
import requests
import json
import time

# Login first
login_url = "http://127.0.0.1:8000/auth/login"
login_data = {
    "username": "jsmith",
    "password": "Aadhithiyan@99"
}

print("🔐 Logging in...")
try:
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens.get("access_token")
        print(f"✅ Login successful!")
        print(f"   Access Token: {access_token[:50]}...")
        
        # Now try to query PID-117
        print("\n📊 Querying PID-117...")
        query_url = "http://127.0.0.1:8000/api/v1/query"
        query_data = {
            "patient_id": "PID-117",
            "question": "What are the patient's primary conditions?",
            "retrieve_k": 5
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        query_response = requests.post(query_url, json=query_data, headers=headers)
        print(f"Status Code: {query_response.status_code}")
        
        if query_response.status_code == 200:
            result = query_response.json()
            print(f"✅ Query successful!")
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
        else:
            print(f"❌ Query failed: {query_response.text}")
    else:
        print(f"❌ Login failed: {login_response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
