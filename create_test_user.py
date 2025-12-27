#!/usr/bin/env python3
"""Create a test user for login"""

import requests
import json

backend_url = "http://127.0.0.1:8000"

# Create user via signup
print("Creating test user...")

signup_data = {
    "username": "jsmith",
    "email": "jsmith@hospital.com",
    "full_name": "Dr. John Smith",
    "password": "Aadhithiyan@99",
    "confirm_password": "Aadhithiyan@99",
    "department": "Internal Medicine",
    "license_number": "MD123456"
}

try:
    response = requests.post(
        f"{backend_url}/auth/signup",
        json=signup_data,
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 201 or response.status_code == 200:
        data = response.json()
        print(f"\n✅ User created successfully!")
        print(f"Username: jsmith")
        print(f"Password: Aadhithiyan@99")
        
        # Try to login
        print("\nAttempting login...")
        login_response = requests.post(
            f"{backend_url}/auth/login",
            json={
                "username": "jsmith",
                "password": "Aadhithiyan@99"
            },
            timeout=10
        )
        
        print(f"Login Status: {login_response.status_code}")
        if login_response.status_code == 200:
            login_data = login_response.json()
            print(f"✅ Login successful!")
            print(f"Token: {login_data.get('access_token', 'N/A')[:50]}...")
        else:
            print(f"Login failed: {login_response.text[:300]}")
    else:
        print(f"❌ Signup failed: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
