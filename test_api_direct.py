"""Direct API test with detailed output"""
import requests
import json

# Login
login_resp = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "jsmith", "password": "password123"}
)

if login_resp.status_code != 200:
    print(f"Login failed: {login_resp.status_code}")
    print(login_resp.text)
    exit(1)

token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get patient details
print("Fetching patient PID-102 details...")
resp = requests.get(
    "http://localhost:8000/api/v1/patients/PID-102/details",
    headers=headers
)

print(f"\nStatus: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    
    print(f"\nPatient: {data.get('name')}")
    print(f"Total Records: {data.get('totalRecords')}")
    
    vitals = data.get('vitals', [])
    print(f"\nVitals: {len(vitals)} found")
    for i, v in enumerate(vitals[:3]):
        print(f"  {i+1}. {v.get('label')}: {v.get('value')} {v.get('unit')}")
    
    meds = data.get('medications', [])
    print(f"\nMedications: {len(meds)} found")
    for i, m in enumerate(meds[:3]):
        print(f"  {i+1}. {m.get('name')}")
    
    conds = data.get('medicalHistory', [])
    print(f"\nConditions: {len(conds)} found")
    for i, c in enumerate(conds[:3]):
        print(f"  {i+1}. {c.get('condition')}")
    
    # Save full response for inspection
    with open('api_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("\nFull response saved to api_response.json")
else:
    print(f"Error: {resp.text}")
