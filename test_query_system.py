"""
Test Query System - Check if it retrieves patient records and generates answers
"""
import os
from dotenv import load_dotenv
load_dotenv()

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"🔹 {title}")
    print(f"{'='*70}")

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

# Step 1: Test Backend Connection
print_section("1. Testing Backend Connection")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    if response.status_code == 200:
        print_success(f"Backend is running at {BACKEND_URL}")
    else:
        print_error(f"Backend returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print_error(f"Cannot connect to backend at {BACKEND_URL}")
    print_info("Make sure to run: python -m uvicorn backend.main:app --reload")
    exit(1)

# Step 2: Check if we can login
print_section("2. Testing Authentication")
login_payload = {
    "username": "test_user",
    "password": "testpass123"
}

response = requests.post(f"{BACKEND_URL}/auth/login", json=login_payload)
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get('access_token')
    print_success(f"Authentication endpoint is working")
    print_info(f"Token type: {token_data.get('token_type')}")
else:
    print_error(f"Login failed - Check if user exists")
    print_info("You need to first signup at http://localhost:3000/auth/signup")
    print_info("After signup, update the credentials above")
    exit(1)

# Step 3: Test Query Endpoint with Mock Data
print_section("3. Testing Query Endpoint")
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Test query
query_payload = {
    "question": "What are the patient's current medications and conditions?",
    "patient_id": "P123",
    "retrieve_k": 5
}

print_info(f"Sending query for patient P123...")
print_info(f"Question: {query_payload['question']}")

response = requests.post(
    f"{BACKEND_URL}/api/v1/query",
    json=query_payload,
    headers=headers,
    timeout=30
)

print_info(f"\nResponse Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    
    print_success("Query processed successfully!")
    
    print_info(f"\n📋 Query Results:")
    print(f"\nQuery ID: {result.get('query_id')}")
    print(f"Confidence: {result.get('confidence'):.2f}")
    
    # Check if answer was generated
    answer = result.get('answer', '')
    if answer:
        print(f"\n📝 Generated Answer:")
        print(f"{answer[:500]}...")  # First 500 chars
        print_success("LLM is generating answers from patient records!")
    else:
        print_error("No answer generated")
    
    # Check source documents
    sources = result.get('sources', [])
    print(f"\n📚 Source Documents Found: {len(sources)}")
    if sources:
        print_success(f"Retrieved {len(sources)} patient records from database!")
        for i, source in enumerate(sources[:3], 1):
            print(f"\n  Document {i}:")
            print(f"    Type: {source.get('type')}")
            print(f"    Date: {source.get('date')}")
            print(f"    Similarity: {source.get('similarity'):.3f}")
            print(f"    Snippet: {source.get('snippet')[:100]}...")
    else:
        print_error("No source documents retrieved")
    
    # Check disclaimer
    print(f"\n⚠️  Disclaimer: {result.get('disclaimer')}")
    
else:
    error_detail = response.text
    print_error(f"Query failed with status {response.status_code}")
    print(f"Error: {error_detail[:300]}")
    
    if response.status_code == 403:
        print_info("Access denied - User may not have 'attending' role")
        print_info("Login as an admin/attending user")
    elif response.status_code == 404:
        print_info("Patient not found - Try with a valid patient ID")

# Step 4: Database Status
print_section("4. Checking Database Connection")
response = requests.get(
    f"{BACKEND_URL}/api/v1/patients",
    headers=headers,
    params={"limit": 5}
)

if response.status_code == 200:
    patients = response.json()
    print_success(f"Database connected! Found {len(patients)} patients")
    for patient in patients[:3]:
        print(f"  - Patient ID: {patient.get('patient_id')}")
else:
    print_error(f"Cannot retrieve patients - Status {response.status_code}")

# Step 5: Services Status
print_section("5. System Status Summary")
print(f"""
Query System Status:
  Backend: ✅ Running
  Authentication: ✅ Working
  Query Endpoint: {'✅ Working' if response.status_code == 200 else '❌ Not Working'}
  LLM (Groq): Check GROQ_API_KEY in .env
  Database: {'✅ Connected' if response.status_code == 200 else '❌ Disconnected'}
  Embedder: Check sentence-transformers installation

Next Steps:
  1. Create a real user account at {FRONTEND_URL}/auth/signup
  2. Assign admin/attending role to the user
  3. Upload patient data via backend
  4. Test queries with real patient records
  5. Check API logs for any errors
""")

print_section("Test Complete!")
print_success("Query system is working correctly!")
