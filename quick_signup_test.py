#!/usr/bin/env python3
"""Test signup endpoint against running backend"""
import requests
import json

def test_signup():
    """Test signup endpoint"""
    signup_data = {
        "username": "newuser_test001",
        "email": "newuser.test001@gmail.com",
        "password": "SecurePass123!",
        "full_name": "New Test User",
        "role": "resident",
        "department": "Cardiology"
    }
    
    try:
        print("Testing signup endpoint...")
        response = requests.post(
            "http://127.0.0.1:8000/auth/signup",
            json=signup_data,
            timeout=10
        )
        print(f"\nResponse status: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ SIGNUP SUCCESS!")
            print(f"Message: {data.get('message')}")
        else:
            print(f"\n✗ SIGNUP FAILED with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to backend at http://127.0.0.1:8000")
        print("Make sure the backend is running with: python run_backend.py")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    test_signup()
