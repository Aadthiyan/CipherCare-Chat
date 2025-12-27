"""
Quick test script to verify patients API endpoint
"""
import requests
import json

# Test credentials (adjust if needed)
BASE_URL = "http://localhost:8000"

def test_patients_api():
    print("\n=== Testing Patients API ===\n")
    
    # Step 1: Login to get token
    print("1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "attending",
            "password": "password123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return
    
    login_data = login_response.json()
    token = login_data.get("access_token")
    print(f"✅ Login successful! Got token: {token[:20]}...")
    
    # Step 2: Fetch patients
    print("\n2. Fetching patients...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    patients_response = requests.get(
        f"{BASE_URL}/api/v1/patients?limit=10",
        headers=headers
    )
    
    if patients_response.status_code != 200:
        print(f"❌ Patients fetch failed: {patients_response.status_code}")
        print(f"   Response: {patients_response.text}")
        return
    
    patients_data = patients_response.json()
    print(f"✅ Patients fetched successfully!")
    print(f"   Total: {patients_data.get('total', 0)}")
    print(f"\nFirst 3 patients:")
    for patient in patients_data.get('patients', [])[:3]:
        print(f"   - {patient['id']}: {patient['name']}")
        print(f"     Gender: {patient['gender']}, DOB: {patient['dob']}")
        print(f"     Conditions: {patient['numConditions']}, Medications: {patient['numMedications']}")
        print(f"     Source: {patient['careProgram']}")
        print()
    
    print(f"\n✅ API is working correctly! {patients_data.get('total', 0)} patients available.")

if __name__ == "__main__":
    try:
        test_patients_api()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running on port 8000?")
    except Exception as e:
        print(f"❌ Error: {e}")
