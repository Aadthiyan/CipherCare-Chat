"""
Test the /api/v1/query endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_query_endpoint():
    print("=" * 60)
    print("Testing CipherCare Query Endpoint")
    print("=" * 60)
    
    # Step 1: Login first
    print("\n[1/3] Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": "attending",
            "password": "password123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    print(f"✓ Login successful! Token: {access_token[:20]}...")
    
    # Step 2: Test query endpoint
    print("\n[2/3] Querying patient data...")
    query_response = requests.post(
        f"{BASE_URL}/api/v1/query",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "patient_id": "P123",
            "question": "What are the latest vitals for this patient?",
            "retrieve_k": 5
        }
    )
    
    print(f"\nStatus Code: {query_response.status_code}")
    
    if query_response.status_code == 200:
        result = query_response.json()
        print("\n✓ Query successful!")
        print(f"\nPatient ID: {result.get('patient_id', 'N/A')}")
        print(f"\nAnswer:\n{'-' * 60}")
        print(result.get('answer', 'N/A'))
        print('-' * 60)
        
        print(f"\nSource Documents: {len(result.get('sources', []))}")
        
        # Show all source documents
        for idx, source in enumerate(result.get('sources', [])[:3], 1):
            print(f"\n  [{idx}] {source.get('document_type', 'Unknown')}")
            print(f"      Date: {source.get('date', 'N/A')}")
            print(f"      Relevance: {source.get('relevance_score', 0):.2f}")
            content = source.get('content', 'N/A')
            print(f"      Content: {content[:150]}{'...' if len(content) > 150 else ''}")
    else:
        print(f"\n❌ Query failed!")
        print(f"Error: {query_response.text}")
    
    # Step 3: Test with different patient
    print("\n[3/3] Testing with different patient (P456)...")
    query_response2 = requests.post(
        f"{BASE_URL}/api/v1/query",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "patient_id": "P456",
            "question": "What medications is this patient currently taking?",
            "retrieve_k": 3
        }
    )
    
    print(f"Status Code: {query_response2.status_code}")
    if query_response2.status_code == 200:
        result2 = query_response2.json()
        print(f"✓ Query successful for P456!")
        print(f"Answer preview: {result2.get('answer', 'N/A')[:150]}...")
    else:
        print(f"❌ Query failed: {query_response2.text}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_query_endpoint()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend at http://localhost:8000")
        print("Make sure the backend is running!")
    except Exception as e:
        print(f"❌ ERROR: {e}")
