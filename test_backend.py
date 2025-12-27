import requests
import json
import sys

BASE_URL = "http://localhost:8008"

def run_tests():
    print("1. Testing Health...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        print("Health Response:", r.json())
    except Exception as e:
        print(f"Health Failed: {e}")
        return

    print("\n2. Getting Token...")
    try:
        payload = {
            "username": "attending",
            "password": "password123"
        }
        r = requests.post(f"{BASE_URL}/token", data=payload) # Form data
        if r.status_code != 200:
            print(f"Token Failed: {r.status_code} {r.text}")
            return
        token = r.json()["access_token"]
        print("Token Acquired.")
    except Exception as e:
        print(f"Token Failed: {e}")
        return

    print("\n3. Testing Query (RAG)...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Updated Spec
        query_payload = {
            "patient_id": "P123", # User 'attending' has 'any' access or we use a valid ID
            "question": "What conditions does the patient have?",
            "retrieve_k": 3,
            "temperature": 0.5
        }
        r = requests.post(f"{BASE_URL}/api/v1/query", json=query_payload, headers=headers)
        if r.status_code != 200:
            print(f"Query Failed: {r.status_code} {r.text}")
        else:
            print("Query Response:", json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Query Failed: {e}")

if __name__ == "__main__":
    run_tests()
