#!/usr/bin/env python3
"""Quick signup test to verify email verification system"""
import sys
import time
import subprocess
import requests
import json

def test_signup():
    """Test signup endpoint"""
    # Start backend in background
    print("Starting backend server...")
    backend_proc = subprocess.Popen(
        [sys.executable, "run_backend.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("Waiting 30 seconds for server to initialize...")
    time.sleep(30)
    
    # Test signup
    print("\nTesting signup endpoint...")
    signup_data = {
        "username": "newuser_dec26",
        "email": "test.dec26@gmail.com",
        "password": "SecurePass123!",
        "full_name": "Test User Dec 26",
        "role": "resident",
        "department": "Cardiology"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/auth/signup",
            json=signup_data,
            timeout=10
        )
        print(f"\nResponse status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ SIGNUP SUCCESS!")
            print(f"User created: {data.get('user', {}).get('username')}")
            print(f"Email: {data.get('user', {}).get('email')}")
            print(f"Verification required: {data.get('verification_required')}")
        else:
            print(f"\n✗ SIGNUP FAILED with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to backend server at http://127.0.0.1:8000")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        # Kill backend
        backend_proc.terminate()
        print("\nBackend server stopped.")

if __name__ == "__main__":
    test_signup()
