#!/usr/bin/env python3
"""Test signup to see exact error"""
import requests
import json

signup_data = {
    "username": "testuser123",
    "email": "test123@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User 123",
    "role": "resident",
    "department": ""  # Empty string
}

print("Sending signup request with data:")
print(json.dumps(signup_data, indent=2))
print()

try:
    response = requests.post(
        "http://127.0.0.1:8000/auth/signup",
        json=signup_data,
        timeout=10
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
