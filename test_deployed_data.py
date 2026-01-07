"""
Quick test to check if patient data is available in deployed CyborgDB
"""

import requests
import json

# Your deployed backend URL (from Render logs)
BACKEND_URL = "https://ciphercare-chat.onrender.com"

print("=" * 70)
print("🧪 Testing Deployed CyborgDB - Patient Data Availability")
print("=" * 70)

# Test 1: Health Check
print("\n1️⃣ Testing backend health...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=10)
    if response.status_code == 200:
        print(f"   ✅ Backend is healthy: {response.json()}")
    else:
        print(f"   ❌ Backend health check failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Get Patients List
print("\n2️⃣ Testing patient list endpoint...")
try:
    response = requests.get(f"{BACKEND_URL}/api/v1/patients", timeout=10)
    if response.status_code == 200:
        patients = response.json()
        print(f"   ✅ Found {len(patients)} patients")
        if len(patients) > 0:
            print(f"   Sample patients: {patients[:5]}")
    else:
        print(f"   ⚠️  Status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Try a Simple Query (requires auth token)
print("\n3️⃣ Testing query endpoint (without auth - will show if endpoint exists)...")
try:
    response = requests.post(
        f"{BACKEND_URL}/api/v1/query",
        json={
            "patient_id": "PID-101",
            "question": "What medications is this patient taking?",
            "retrieve_k": 5
        },
        timeout=30
    )
    
    if response.status_code == 401:
        print(f"   ✅ Query endpoint exists (needs authentication)")
    elif response.status_code == 200:
        result = response.json()
        print(f"   ✅ Query successful!")
        print(f"   Answer: {result.get('answer', 'N/A')[:100]}...")
        print(f"   Sources: {len(result.get('sources', []))} records found")
    else:
        print(f"   ⚠️  Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("📊 Summary")
print("=" * 70)
print("\nIf you see:")
print("  ✅ Backend is healthy")
print("  ✅ Found patients")
print("  ✅ Query endpoint exists")
print("\nThen your deployment is working!")
print("\nNext: Test with actual authentication from your frontend")
print("=" * 70)
