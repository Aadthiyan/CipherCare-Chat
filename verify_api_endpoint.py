#!/usr/bin/env python3
"""Test the /api/v1/patients endpoint to verify it's working"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BACKEND_URL}/auth/login"
PATIENTS_URL = f"{BACKEND_URL}/api/v1/patients"

print("\n" + "="*60)
print("TESTING /api/v1/patients ENDPOINT")
print("="*60)

# Login with test credentials
print("\n1️⃣  Logging in...")
login_data = {
    "username": "jsmith",
    "password": "test123"
}

try:
    login_response = requests.post(LOGIN_URL, json=login_data)
    print(f"   Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data.get('access_token')
        print(f"   ✅ Login successful")
        
        # Query patients with the token
        print("\n2️⃣  Fetching patients with token...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        patients_response = requests.get(PATIENTS_URL, headers=headers)
        print(f"   Status: {patients_response.status_code}")
        
        if patients_response.status_code == 200:
            patients_data = patients_response.json()
            total = patients_data.get('total', 0)
            print(f"   ✅ Success! Found {total} patients")
            print(f"\n   Response:")
            print(f"   {json.dumps(patients_data, indent=2)}")
        else:
            print(f"   ❌ Error {patients_response.status_code}")
            print(f"   {patients_response.text}")
    else:
        error_msg = login_response.json()
        print(f"   ❌ Login failed: {error_msg}")
        print(f"\n   Try these credentials:")
        print(f"   Username: jsmith")
        print(f"   Password: (the password you set during signup)")
        
except requests.exceptions.ConnectionError:
    print(f"   ❌ Cannot connect to backend at {BACKEND_URL}")
    print(f"   Is the backend running? python run_backend.py")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60 + "\n")
