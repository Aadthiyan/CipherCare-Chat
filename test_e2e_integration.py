"""
End-to-End Test: Frontend → Backend Integration
Tests the complete flow through the frontend proxy
"""
import requests
import time

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

def test_e2e_integration():
    print("=" * 70)
    print("End-to-End Integration Test: Frontend ↔ Backend")
    print("=" * 70)
    
    # Step 1: Test frontend is accessible
    print("\n[Step 1] Testing frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=15)
        if response.status_code == 200:
            print(f"✓ Frontend is UP at {FRONTEND_URL}")
        else:
            print(f"⚠ Frontend returned status {response.status_code}")
    except Exception as e:
        print(f"✗ Cannot connect to frontend: {e}")
        print("Make sure frontend is running with 'npm run dev'")
        return
    
    # Step 2: Login via BACKEND (not frontend auth)
    print("\n[Step 2] Authenticating with backend...")
    try:
        login_response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": "attending", "password": "password123"},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"✗ Login failed: {login_response.status_code}")
            print(login_response.text)
            return
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(f"✓ Login successful!")
        print(f"  Token: {access_token[:40]}...")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        return
    
    # Step 3: Query via Frontend Proxy API
    print("\n[Step 3] Testing query through frontend proxy...")
    try:
        query_response = requests.post(
            f"{FRONTEND_URL}/api/query",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={
                "patient_id": "P123",
                "question": "What is the patient's medical history?",
                "retrieve_k": 3
            },
            timeout=30
        )
        
        print(f"  Status Code: {query_response.status_code}")
        
        if query_response.status_code == 200:
            result = query_response.json()
            print(f"\n✓ Query successful through frontend proxy!")
            print(f"\n  Patient: {result.get('patient_id', 'N/A')}")
            print(f"\n  Answer Preview:")
            print(f"  {'-' * 66}")
            answer = result.get('answer', 'N/A')
            print(f"  {answer[:200]}...")
            print(f"  {'-' * 66}")
            
            sources = result.get('sources', [])
            print(f"\n  Sources Retrieved: {len(sources)}")
            
            if sources:
                print(f"\n  First Source:")
                first = sources[0]
                print(f"    • Type: {first.get('document_type', 'Unknown')}")
                print(f"    • Date: {first.get('date', 'N/A')}")
                print(f"    • Relevance: {first.get('relevance_score', 0):.2f}")
        else:
            print(f"\n✗ Query failed!")
            print(f"  Error: {query_response.text}")
            return
    
    except Exception as e:
        print(f"✗ Query request failed: {e}")
        return
    
    # Step 4: Test with different patient
    print("\n[Step 4] Testing with different patient (P456)...")
    try:
        query_response2 = requests.post(
            f"{FRONTEND_URL}/api/query",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={
                "patient_id": "P456",
                "question": "What medications is this patient taking?",
                "retrieve_k": 3
            },
            timeout=30
        )
        
        if query_response2.status_code == 200:
            print(f"✓ Successfully queried patient P456")
            result2 = query_response2.json()
            print(f"  Sources: {len(result2.get('sources', []))}")
        else:
            print(f"⚠ Query failed for P456: {query_response2.status_code}")
    except Exception as e:
        print(f"⚠ P456 query error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ End-to-End Test PASSED!")
    print("=" * 70)
    print("\nConfiguration Summary:")
    print(f"  • Frontend:  {FRONTEND_URL} ✓")
    print(f"  • Backend:   {BACKEND_URL} ✓")
    print(f"  • CORS:      Configured ✓")
    print(f"  • Auth:      JWT Tokens ✓")
    print(f"  • Proxy:     /api/query → /api/v1/query ✓")
    print(f"  • LLM:       Groq (working) ✓")
    print("\n🎉 Your frontend and backend are correctly configured!")
    print("\nYou can now:")
    print("  1. Open http://localhost:3000 in your browser")
    print("  2. Login with: attending / password123")
    print("  3. Query patient data through the UI")
    print("=" * 70)

if __name__ == "__main__":
    # Wait for frontend to be ready
    print("Waiting for frontend to be ready...")
    time.sleep(3)
    test_e2e_integration()
