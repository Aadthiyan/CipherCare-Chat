#!/usr/bin/env python3
"""Check CyborgDB for patient data and test query functionality"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BACKEND_URL}/auth/login"
QUERY_URL = f"{BACKEND_URL}/api/v1/query"
PATIENTS_URL = f"{BACKEND_URL}/api/v1/patients"

print("\n" + "="*70)
print("CHECKING CYBORGDB FOR PATIENT DATA & TESTING QUERY")
print("="*70)

# Step 1: Login
print("\n1️⃣  LOGGING IN...")
try:
    # Try to get jsmith user's password from database or use a test password
    login_response = requests.post(LOGIN_URL, json={
        "username": "jsmith",
        "password": "test123"
    })
    
    if login_response.status_code == 401:
        print("   ⚠️  Login failed. Let me check available users...")
        # Try with a different approach
        print("   Creating test user...")
        signup_url = f"{BACKEND_URL}/auth/signup"
        signup_resp = requests.post(signup_url, json={
            "username": "testuser",
            "email": "test@test.com",
            "password": "Test@123",
            "full_name": "Test User",
            "role": "attending"
        })
        print(f"   Signup response: {signup_resp.status_code}")
        if signup_resp.status_code == 200:
            data = signup_resp.json()
            user_id = data.get('user', {}).get('id')
            print(f"   User created: {user_id}")
            # For this demo, skip OTP and go to existing user
    else:
        data = login_response.json()
        access_token = data.get('access_token')
        print(f"   ✅ Logged in successfully")
        
        # Step 2: Get patients list
        print("\n2️⃣  FETCHING PATIENT LIST...")
        headers = {"Authorization": f"Bearer {access_token}"}
        patients_resp = requests.get(PATIENTS_URL, headers=headers)
        
        if patients_resp.status_code == 200:
            patients_data = patients_resp.json()
            patient_count = patients_data.get('total', 0)
            print(f"   ✅ Found {patient_count} patients")
            
            if patient_count > 0:
                patients = patients_data.get('patients', [])
                test_patient = patients[0]
                patient_id = test_patient['id']
                patient_name = test_patient['name']
                
                print(f"   Sample patient: {patient_id} - {patient_name}")
                print(f"   Age: {test_patient.get('age')}, Gender: {test_patient.get('gender')}")
                print(f"   Condition: {test_patient.get('condition')}")
                
                # Step 3: Test query with real patient
                print(f"\n3️⃣  TESTING QUERY WITH PATIENT {patient_id}...")
                query_payload = {
                    "patient_id": patient_id,
                    "query": f"What are the medical conditions for {patient_name}?"
                }
                
                print(f"   Query: {query_payload['query']}")
                
                query_resp = requests.post(QUERY_URL, json=query_payload, headers=headers)
                
                print(f"   Response status: {query_resp.status_code}")
                
                if query_resp.status_code == 200:
                    query_data = query_resp.json()
                    result = query_data.get('result', '')
                    
                    print(f"\n   ✅ QUERY SUCCESSFUL!")
                    print(f"   Response from AI:")
                    print(f"   {result[:500]}..." if len(result) > 500 else f"   {result}")
                    
                    # Check metadata
                    if 'metadata' in query_data:
                        print(f"\n   Metadata:")
                        print(f"   - Search type: {query_data['metadata'].get('search_type')}")
                        print(f"   - Results found: {query_data['metadata'].get('results_found')}")
                        print(f"   - Source: {query_data['metadata'].get('source')}")
                        
                elif query_resp.status_code == 403:
                    print(f"   ❌ ACCESS DENIED")
                    print(f"   {query_resp.json()}")
                else:
                    print(f"   ❌ Query failed: {query_resp.status_code}")
                    print(f"   {query_resp.text}")
                    
        else:
            print(f"   ❌ Failed to fetch patients: {patients_resp.status_code}")
            print(f"   {patients_resp.text}")
            
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*70)
print("CHECKING CYBORGDB DIRECTLY")
print("="*70)

# Check CyborgDB Lite status
cyborg_url = "http://localhost:8002"
print(f"\n4️⃣  CHECKING CYBORGDB AT {cyborg_url}...")

try:
    # Try to list collections
    collections_resp = requests.get(f"{cyborg_url}/collections")
    print(f"   Collections endpoint status: {collections_resp.status_code}")
    
    if collections_resp.status_code == 200:
        collections = collections_resp.json()
        print(f"   ✅ Collections available: {collections}")
    else:
        print(f"   ⚠️  Could not fetch collections: {collections_resp.text[:200]}")
        
except Exception as e:
    print(f"   ⚠️  CyborgDB not responding: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("""
If patient data shows in step 2, it means:
- ✅ Patient data is being loaded from synthea_patients_221.json
- ✅ Backend /api/v1/patients endpoint is working
- ✅ Patient data IS accessible via API

If query works in step 3, it means:
- ✅ CyborgDB has the patient data (or mock data)
- ✅ Query endpoint can search/retrieve patient info
- ✅ LLM can process and respond to queries

Note: Currently loading from JSON file, not stored in CyborgDB itself.
To store in CyborgDB permanently, run:
  python upload_local_patients.py
""")
print("="*70 + "\n")
