#!/usr/bin/env python3
"""Test OTP verification flow"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_signup_with_otp():
    """Test signup and OTP verification"""
    print("=" * 60)
    print("OTP VERIFICATION FLOW TEST")
    print("=" * 60)
    
    # Step 1: Signup
    print("\n[1/3] Testing Signup...")
    signup_data = {
        "username": "otp_test_user",
        "email": "otp.test@example.com",
        "password": "SecurePass123!",
        "full_name": "OTP Test User",
        "role": "resident",
        "department": "Testing"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json=signup_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Signup failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        user_id = data.get('user', {}).get('id')
        otp_code = data.get('otp_code')
        
        print(f"✓ Signup successful!")
        print(f"  User ID: {user_id}")
        print(f"  OTP Code: {otp_code}")
        print(f"  Message: {data.get('message')}")
        
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return
    
    # Step 2: Verify OTP
    print("\n[2/3] Testing OTP Verification...")
    
    try:
        verify_data = {
            "user_id": user_id,
            "otp_code": otp_code
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/verify-otp",
            json=verify_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ OTP verification failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        print(f"✓ OTP verification successful!")
        print(f"  Message: {data.get('message')}")
        
    except Exception as e:
        print(f"❌ OTP verification error: {e}")
        return
    
    # Step 3: Test Login
    print("\n[3/3] Testing Login with Verified Account...")
    
    try:
        login_data = {
            "username": "otp_test_user",
            "password": "SecurePass123!"
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        token = data.get('access_token')
        
        print(f"✓ Login successful!")
        print(f"  Token: {token[:30]}...")
        print(f"  Token Type: {data.get('token_type')}")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_signup_with_otp()
