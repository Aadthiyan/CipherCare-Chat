#!/usr/bin/env python
"""Test authentication endpoints"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("TESTING AUTHENTICATION ENDPOINTS")
print("=" * 60)

# Test 1: Login with demo credentials
print("\n1. Testing /auth/login endpoint...")
print("-" * 60)

login_data = {
    "username": "attending",
    "password": "password123"
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Status Code: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2))

if response.status_code == 200:
    print("✓ Login successful!")
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    user = result.get("user")
    print(f"  - User: {user['full_name']}")
    print(f"  - Roles: {user['roles']}")
    print(f"  - Token expires in: {result.get('expires_in')} seconds")
else:
    print("✗ Login failed!")
    exit(1)

# Test 2: Get current user with token
print("\n2. Testing /auth/me endpoint...")
print("-" * 60)

headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"Status Code: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2))

if response.status_code == 200:
    print("✓ /auth/me successful!")
else:
    print("✗ /auth/me failed!")

# Test 3: Test signup
print("\n3. Testing /auth/signup endpoint...")
print("-" * 60)

signup_data = {
    "username": "newdoctor",
    "email": "newdoctor@hospital.com",
    "password": "NewPass123!",
    "full_name": "Dr. New Doctor",
    "role": "resident",
    "department": "Cardiology"
}

response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
print(f"Status Code: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2))

if response.status_code == 200:
    print("✓ Signup successful!")
    new_user = result.get("user")
    print(f"  - New user: {new_user['full_name']}")
    print(f"  - Role: {new_user['roles']}")
else:
    print("✗ Signup failed!")

# Test 4: Login with new user
print("\n4. Testing login with newly created user...")
print("-" * 60)

new_login_data = {
    "username": signup_data["username"],
    "password": signup_data["password"]
}

response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data)
print(f"Status Code: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2))

if response.status_code == 200:
    print("✓ New user login successful!")
    new_access_token = result.get("access_token")
    new_user = result.get("user")
    print(f"  - Logged in as: {new_user['full_name']}")
else:
    print("✗ New user login failed!")

# Test 5: Test refresh token
print("\n5. Testing /auth/refresh endpoint...")
print("-" * 60)

if response.status_code == 200:
    refresh_token_data = {
        "refresh_token": result.get("refresh_token")
    }
    
    response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_token_data)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    if response.status_code == 200:
        print("✓ Token refresh successful!")
    else:
        print("✗ Token refresh failed!")

print("\n" + "=" * 60)
print("AUTHENTICATION TESTING COMPLETE")
print("=" * 60)
