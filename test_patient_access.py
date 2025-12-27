#!/usr/bin/env python3
"""Check patient access and test query"""

import requests
import json

# Get token
print("1. Authenticating...")
r_login = requests.post('http://127.0.0.1:8000/auth/login', 
    json={'username': 'jsmith', 'password': 'Aadhithiyan@99'}, 
    timeout=5)
token = r_login.json()['access_token']
print(f"✅ Login successful")

# Get patient list
print("\n2. Getting patient list...")
r_patients = requests.get('http://127.0.0.1:8000/api/v1/patients', 
    headers={'Authorization': f'Bearer {token}'}, 
    timeout=10)

print(f"Status: {r_patients.status_code}")
data = r_patients.json()
patients_list = data.get('patients', [])
print(f"Total patients: {len(patients_list)}")

if patients_list:
    print(f"\nFirst 5 patients:")
    for p in patients_list[:5]:
        print(f"  - {p.get('id')}: {p.get('name')}")
    
    # Try query with first patient
    patient_id = patients_list[0]['id']
    print(f"\n3. Testing query with patient {patient_id}...")
    
    r_query = requests.post(
        'http://127.0.0.1:8000/api/v1/query',
        json={
            'patient_id': patient_id,
            'question': 'What are the main health conditions and medications?'
        },
        headers={'Authorization': f'Bearer {token}'},
        timeout=60
    )
    
    print(f"Status: {r_query.status_code}")
    
    if r_query.status_code == 200:
        result = r_query.json()
        print(f"\n✅ QUERY SUCCESSFUL!\n")
        print(f"Response:\n{result.get('response')}")
    else:
        print(f"Response: {r_query.text[:500]}")
